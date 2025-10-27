Connect-MicrosoftTeams

$teams = Get-Team

$result = @()

foreach ($team in $teams) {
    $owners = (Get-TeamUser -GroupId $team.GroupId -Role Owner).User
    $members = (Get-TeamUser -GroupId $team.GroupId -Role Member).User
    $channels = (Get-TeamChannel -GroupId $team.GroupId).DisplayName

    $result += [PSCustomObject]@{
        TeamName   = $team.DisplayName
        GroupId    = $team.GroupId
        Owners     = ($owners -join ", ")
        Members    = ($members -join ", ")
        Channels   = ($channels -join ", ")
    }
}

$result | Export-Csv -Path "TeamsFullInfo.csv" -NoTypeInformation -Encoding UTF8