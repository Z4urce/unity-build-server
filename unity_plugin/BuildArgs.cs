using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEngine;

namespace Editor.Builder
{
    public struct BuildArgs
    {
        public string Env;
        public string BuildPath;
        public BuildTarget BuildTarget;
        public string ProjectVersion;
        public int BuildNumber;

        public BuildArgs(IReadOnlyList<string> args)
        {
            // Default values
            Env = "Development";
            BuildPath = Path.Combine(Environment.CurrentDirectory, $"{DateTime.UtcNow:dd_MM_yyyy}.apk");
            BuildTarget = BuildTarget.Android;
            ProjectVersion = "1.0.0";
            BuildNumber = 0;
            
            int argsLen = args.Count;
            for (var i = 0; i < argsLen; i++)
            {
                if (args[i] == "-env" && i + 1 < argsLen)
                    Env = args[i + 1];
                
                if (args[i] == "-projectVersion" && i + 1 < argsLen)
                    ProjectVersion = args[i + 1];

                if (args[i] == "-buildPath" && i + 1 < argsLen)
                    BuildPath = args[i + 1];

                if (args[i] == "-buildTarget" && i + 1 < argsLen)
                    BuildTarget = (BuildTarget) Enum.Parse(typeof(BuildTarget), args[i + 1]);

                if (args[i] == "-buildNumber" && i + 1 < argsLen)
                {
                    if (!int.TryParse(args[i + 1], out BuildNumber))
                    {
                        Debug.LogError("Could not parse to int. input="+args[i + 1]);
                    }

                }
            }
        }
    }
}