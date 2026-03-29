using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;

record Finding(string Severity, string File, string Issue, string Recommendation);

static class Env
{
    public static string Require(string name)
    {
        var value = Environment.GetEnvironmentVariable(name);
        if (string.IsNullOrWhiteSpace(value))
        {
            throw new InvalidOperationException($"Missing required environment variable: {name}");
        }

        return value;
    }
}

var token = Env.Require("GITHUB_TOKEN");
var repository = Env.Require("GITHUB_REPOSITORY");
var eventPath = Env.Require("GITHUB_EVENT_PATH");

using var http = new HttpClient();
http.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);
http.DefaultRequestHeaders.Accept.Add(new MediaTypeWithQualityHeaderValue("application/vnd.github+json"));
http.DefaultRequestHeaders.Add("X-GitHub-Api-Version", "2022-11-28");
http.DefaultRequestHeaders.UserAgent.ParseAdd("ai-code-review-mvp-csharp");

var eventJson = await File.ReadAllTextAsync(eventPath);
using var eventDoc = JsonDocument.Parse(eventJson);
if (!eventDoc.RootElement.TryGetProperty("pull_request", out var pr))
{
    Console.WriteLine("No pull_request payload found. Exiting.");
    return;
}

var prNumber = pr.GetProperty("number").GetInt32();
var commentsUrl = pr.GetProperty("comments_url").GetString() ?? throw new InvalidOperationException("Missing comments_url");

var findings = new List<Finding>();
var filesChanged = 0;

for (var page = 1; ; page++)
{
    var filesUrl = $"https://api.github.com/repos/{repository}/pulls/{prNumber}/files?per_page=100&page={page}";
    using var filesResponse = await http.GetAsync(filesUrl);
    filesResponse.EnsureSuccessStatusCode();
    var filesText = await filesResponse.Content.ReadAsStringAsync();

    using var filesDoc = JsonDocument.Parse(filesText);
    if (filesDoc.RootElement.ValueKind != JsonValueKind.Array || filesDoc.RootElement.GetArrayLength() == 0)
    {
        break;
    }

    foreach (var file in filesDoc.RootElement.EnumerateArray())
    {
        filesChanged++;
        var filename = file.TryGetProperty("filename", out var nameProp) ? nameProp.GetString() ?? "unknown" : "unknown";
        var patch = file.TryGetProperty("patch", out var patchProp) ? patchProp.GetString() : null;

        if (string.IsNullOrEmpty(patch))
        {
            continue;
        }

        var checks = new (string Pattern, string Severity, string Issue, string Recommendation)[]
        {
            ("(?i)password\\s*=\\s*['\"]", "blocker", "Possible hardcoded password", "Move secret to secure vault/env vars."),
            ("(?i)api[_-]?key\\s*=\\s*['\"]", "blocker", "Possible hardcoded API key", "Use secret manager or CI secret store."),
            ("\\beval\\(", "blocker", "Use of eval detected", "Replace with safe parser/explicit mapping."),
            ("\\bexec\\(", "blocker", "Use of exec detected", "Avoid dynamic code execution on runtime input."),
            ("TODO", "low", "TODO marker left in patch", "Resolve TODO or create an issue reference."),
        };

        foreach (var (pattern, severity, issue, recommendation) in checks)
        {
            if (Regex.IsMatch(patch, pattern))
            {
                findings.Add(new Finding(severity, filename, issue, recommendation));
            }
        }
    }
}

var commentBody = BuildComment(findings, filesChanged);
var payload = JsonSerializer.Serialize(new { body = commentBody });
using var content = new StringContent(payload, Encoding.UTF8, "application/json");
using var commentResponse = await http.PostAsync(commentsUrl, content);
commentResponse.EnsureSuccessStatusCode();

Console.WriteLine($"Posted AI review summary for PR #{prNumber} with {findings.Count} finding(s).");

static string BuildComment(List<Finding> findings, int filesChanged)
{
    var sb = new StringBuilder();
    sb.AppendLine("## 🤖 AI Code Review (MVP, C#)");
    sb.AppendLine($"Reviewed files: **{filesChanged}**");
    sb.AppendLine();

    if (findings.Count == 0)
    {
        sb.AppendLine("✅ No high-signal issues detected by MVP heuristics.");
        sb.AppendLine();
        sb.AppendLine("_Note: this is a baseline rule-based pass. Add LLM + repository context for deeper review._");
        return sb.ToString();
    }

    sb.AppendLine("| severity | file | issue | recommendation |");
    sb.AppendLine("|---|---|---|---|");

    foreach (var finding in findings)
    {
        sb.AppendLine($"| {finding.Severity} | `{finding.File}` | {finding.Issue} | {finding.Recommendation} |");
    }

    return sb.ToString();
}
