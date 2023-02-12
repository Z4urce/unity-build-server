#if UNITY_IOS
using System.IO;
using UnityEditor;
using UnityEditor.Callbacks;
using UnityEditor.iOS.Xcode;
using UnityEngine;

namespace Editor.Builder
{
    public class XcodeBuildPostProcessor
    {
        private const string BundleId = "com.company.${PRODUCT_NAME}";
        private const string ProvisionFile = "ios.mobileprovision";
        private const string ExportMethod = "app-store";

        [PostProcessBuild]
        public static void ChangeXcodePlist(BuildTarget target, string buildPath) {
            // We don't have to do anything if it's not ios
            if (target != BuildTarget.iOS) {
                return;
            }

            // Get plist
            string plistPath = buildPath + "/Info.plist";
            PlistDocument plist = new PlistDocument();
            plist.ReadFromString(File.ReadAllText(plistPath));

            // Get root
            PlistElementDict rootDict = plist.root;

            // Write values
            rootDict.SetString("method", ExportMethod);
            var provisioningProfiles = rootDict.CreateDict("provisioningProfiles");

            string projectPath = Directory.GetParent(Application.dataPath).ToString();
            string provisionPath = Path.Combine(projectPath, ProvisionFile);

            provisioningProfiles.SetString(BundleId, provisionPath);

            // Write to file
            File.WriteAllText(plistPath, plist.WriteToString());
        }
    }
}

#endif
