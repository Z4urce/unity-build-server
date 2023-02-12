param (
    [Parameter(Mandatory=$true)][string]$buildPath
 )

cd $buildPath
if (Test-Path "Unity-iPhone.xcworkspace")
{
  xcodebuild -workspace Unity-iPhone.xcworkspace -scheme "Unity-iPhone" -sdk iphoneos -configuration Release archive -archivePath export/build/app.xcarchive
}
else {
  xcodebuild -project Unity-iPhone.xcodeproj -scheme "Unity-iPhone" -sdk iphoneos -configuration Release archive -archivePath export/build/app.xcarchive
}

if (!$?) {
    throw "xcodebuild failed. Exiting with code 1"
    exit 1
}

xcodebuild -exportArchive -archivePath export/build/app.xcarchive -exportOptionsPlist info.plist -exportPath export/build
& xcrun altool --upload-app -f "export/build/Unity-iPhone.ipa" -u "[MAIL HERE]" -p "[PASSWORD HERE]"

if (!$?) {
    throw "exportArchive failed. Exiting with code 1"
    exit 1
}