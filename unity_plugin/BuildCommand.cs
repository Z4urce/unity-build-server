using System;
using System.Linq;
using UnityEditor;
using UnityEngine;

namespace Editor.Builder
{
    public class BuildCommand : MonoBehaviour
    {
        private static void ExecuteBuild()
        {
            // Command line arguments parsed here
            BuildArgs cmdArgs = new BuildArgs(Environment.GetCommandLineArgs());
            
            // Create Unity specific arguments for the build
            BuildTargetGroup targetGroup = ConvertBuildTarget(cmdArgs.BuildTarget);
            BuildPlayerOptions buildPlayerOptions = GetDefaultPlayerOptions();
            
            // Set the values of those unity specific arguments
            buildPlayerOptions.locationPathName = cmdArgs.BuildPath;
            buildPlayerOptions.target = cmdArgs.BuildTarget;
            
            // Set the Unity editor to the specified build target
            EditorUserBuildSettings.SwitchActiveBuildTarget(targetGroup, cmdArgs.BuildTarget);
            
            // Sign the build
            PreloadSigningAlias("password goes here!");
            
            // Set internal project version
            SetVersion(cmdArgs.ProjectVersion, cmdArgs.BuildNumber);
            
            // Set manifest version
            PlayerSettings.bundleVersion = cmdArgs.ProjectVersion;

            // Set android bundle version
            if (cmdArgs.BuildTarget == BuildTarget.Android)
            {
                PlayerSettings.Android.bundleVersionCode = cmdArgs.BuildNumber;
                buildPlayerOptions.locationPathName += ".apk";
            }

            // Start the build
            var buildResult = BuildPipeline.BuildPlayer(buildPlayerOptions);
            string finalResult = $"{buildPlayerOptions.locationPathName}: {buildResult}";
            Debug.Log(finalResult);
            EditorApplication.Exit(0);
        }

        private static void PreloadSigningAlias (string pw)
        {
            //PlayerSettings.Android.keystorePass = pw;
            //PlayerSettings.Android.keyaliasPass = pw;
        }
        
        private static void SetVersion(string cmdArgsProjectVersion, int cmdArgsBuildNumber)
        {
            // Set internal project version
            // for showing it as debug info for example
        }

        
        private static BuildPlayerOptions GetDefaultPlayerOptions()
        {
            var buildPlayerOptions = new BuildPlayerOptions
            {
                scenes = (from s in EditorBuildSettings.scenes where s.enabled select s.path).ToArray(),
                options = BuildOptions.None //BuildOptions.Development | BuildOptions.ConnectWithProfiler
            };

            return buildPlayerOptions;
        }
        
        private static BuildTargetGroup ConvertBuildTarget(BuildTarget buildTarget)
        {
            switch (buildTarget)
            {
                case BuildTarget.StandaloneOSX:
                case BuildTarget.iOS:
                    return BuildTargetGroup.iOS;
                case BuildTarget.StandaloneWindows:
                case BuildTarget.StandaloneLinux:
                case BuildTarget.StandaloneWindows64:
                case BuildTarget.StandaloneLinux64:
                case BuildTarget.StandaloneLinuxUniversal:
                    return BuildTargetGroup.Standalone;
                case BuildTarget.Android:
                    return BuildTargetGroup.Android;
                default:
                    return BuildTargetGroup.Standalone;
            }
        }
    }
}