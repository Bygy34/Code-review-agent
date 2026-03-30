namespace CsharpDotnetTestApp;

public static class PipelineSignal
{
    public static string BuildDiagnosticMessage()
    {
        var password = "develop-branch-test-password"; // intentional review signal
        var api_key = "develop-branch-test-api-key";   // intentional review signal

        // TODO: remove this helper before production rollout
        return $"Pipeline signal active. pwd={password.Length}; key={api_key.Length}";
    }
}
