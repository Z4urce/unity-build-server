param (
    [Parameter(Mandatory=$true)][string]$workspacePath
 )

 <#
cd $workspacePath
$statusRaw = cm status --nochanges
$changesetId = $statusRaw.Split(":", 2).Split("@", 2)[1]
$branch = cm find changeset where changesetid "=" $changesetId --format="{branch}" --nototal
$csList = cm find changeset where branch="'$branch'" and changesetid ">" $changesetId --format="[{changesetid}] {comment}" --nototal

$csList
#>

cd $workspacePath
git fetch -p -q
$actualBranch = git rev-parse --abbrev-ref HEAD
git log --format=format:"%s - %an (%cr)" --no-merges HEAD..origin/$actualBranch