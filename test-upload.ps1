$boundary = [guid]::NewGuid().ToString()
$filePath = "D:\tmp\test.xlsx"
$fileName = "test.xlsx"
$fileBytes = [System.IO.File]::ReadAllBytes($filePath)

$header = "--$boundary`r`n" +
    "Content-Disposition: form-data; name=`"file`"; filename=`"$fileName`"`r`n" +
    "Content-Type: application/octet-stream`r`n`r`n"

$footer = "`r`n--$boundary--`r`n"

$headerBytes = [System.Text.Encoding]::UTF8.GetBytes($header)
$footerBytes = [System.Text.Encoding]::UTF8.GetBytes($footer)

$body = New-Object byte[] ($headerBytes.Length + $fileBytes.Length + $footerBytes.Length)
[Array]::Copy($headerBytes, 0, $body, 0, $headerBytes.Length)
[Array]::Copy($fileBytes, 0, $body, $headerBytes.Length, $fileBytes.Length)
[Array]::Copy($footerBytes, 0, $body, $headerBytes.Length + $fileBytes.Length, $footerBytes.Length)

$request = [System.Net.HttpWebRequest]::Create("http://localhost:3000/api/upload")
$request.Method = "POST"
$request.ContentType = "multipart/form-data; boundary=$boundary"
$request.ContentLength = $body.Length

$stream = $request.GetRequestStream()
$stream.Write($body, 0, $body.Length)
$stream.Close()

try {
    $response = $request.GetResponse()
    $reader = New-Object System.IO.StreamReader($response.GetResponseStream())
    $result = $reader.ReadToEnd()
    Write-Host "SUCCESS: $result"
} catch {
    Write-Host "ERROR: $($_.Exception.Message)"
}
