param (
    [Parameter(Mandatory=$true)][string]$workspacePath
 )

cd $workspacePath
git clean -d -f
git reset --hard
git pull
git submodule update --init --
