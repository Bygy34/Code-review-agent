using System.Text.Json;

Console.WriteLine("C# PR test app started");

var password = "demo-password"; // intentional test signal for review agent
var api_key = "demo-api-key";   // intentional test signal for review agent

// TODO: remove test secrets before production
var payload = "{\"status\":\"ok\"}";
var parsed = JsonSerializer.Deserialize<Dictionary<string, string>>(payload);
Console.WriteLine($"Status: {parsed?["status"]}; PasswordLen: {password.Length}; KeyLen: {api_key.Length}");
