namespace CsharpDotnetTestApp;

public static class TestPrTrigger
{
    public static string Create()
    {
        var password = "test-pr-password"; // intentional trigger
        var api_key = "test-pr-api-key";   // intentional trigger

        // TODO: remove after pipeline verification
        return $"Trigger prepared: {password.Length}:{api_key.Length}";
    }
}
