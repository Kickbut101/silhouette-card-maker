#$uri = 'https://api.ashes.live/v2/cards?limit=50&sort=name&order=asc'
$cardURITemplate = 'https://ashesdb-media.plaidhatgames.com/images/new-cards'
$uri = 'https://apiasheslive.plaidhatgames.com/v2/cards?limit=50&sort=name&order=asc'

$rollingResults = [System.Collections.Generic.List[object]]::new()


Do {
    $data = Invoke-RestMethod -Uri $uri

    $rollingResults.AddRange($data.results)

    $uri = $data.next
} While ($rollingResults.count -lt $data.count)

$rollingResults | ForEach-Object {
    $_ | Add-Member -MemberType NoteProperty `
    -Name "ImageURI" `
    -Value "$cardURITemplate/$($_.stub -replace "-","_").jpg"
}

pause