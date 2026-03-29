using System.Text.Json;
using CsharpDotnetTestApp;

Console.WriteLine("C# PR test app started");

var payload = "{\"status\":\"ok\"}";
var parsed = JsonSerializer.Deserialize<Dictionary<string, string>>(payload);

var diagnostic = PipelineSignal.BuildDiagnosticMessage();
Console.WriteLine($"Status: {parsed?["status"]}");
Console.WriteLine(diagnostic);

