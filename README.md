# Unity Build Server
Flask based Unity build server with a web interface.
Version 2.6

## How it works?
1. The server handles HTTP requests over localhost:80.
2. When you start a build trough its web interface, it reads the `projects.cfg` file and choses the config for the specific project.
3. It tries to open the project's own `BuildSettings.txt` file which may contain additional configurations, arguments or overrides. (Not necessary, used to increase version)
4. Executes the value of `updateProjectScript` (Used to pull the latest changes)
5. The server opens unity using all the configuration entries as arguments.
6. Unity runs the static method defined in `executeMethod` (Used to set internal project parameters)
6. After the build is finished, runs `postBuildScript` if exists in configs (Used to upload addressables)


## Installation

1. Use the package manager [pip](https://pip.pypa.io/en/stable/) to install the dependencies.

```bash
pip install flask
pip install psutil
```

2. Configure the server as it is written bellow
3. Copy the contents of the `unity_plugin` directory into your Unity project assets. You can modify it to your heart's content, as it will be certainly unique for each project.
4. Create all necessary directories for your projects. (You might even want to clone them)
5. Run the `_START_SERVER.ps1` (on Windows) or `build_server.py` trough Python

## Config
### How to add your project
Edit the `projects.cfg` file to add a new build project. Example:
```json
[
   {
      "project":"SimpleUnityProject",
      "engineVersion":"2019.1.2f1",
      "executeMethod":"Editor.Builder.BuildCommand.ExecuteBuild",
      "postBuildScript":"scripts/upload_addressables.ps1",
      "updateProjectScript":"scripts/update_workspace_git.ps1",
      "webhookUrl":"Slack/ Discord URL",
      "xcodeScript":"scripts/build_xcode.ps1"
   }
]
```
Here you can add all the fundamental variables to your project, which will be later inherited by **all** build configurations for the project.

### How to add a build configuration to an existing project
Edit (or create) a file called `{project}.project` (SimpleUnityProject.project) in the config directory. This file can extend and override the content for its corresponding project config (mentioned above) Example:
```
   {  
      #This is the name of this configuration
      "name":"SC Dev",
      #Unity engine version
      "engineVersion":"2018.2.14f1",
      #Version of the project, used at naming and passed as argument to Unity
      "projectVersion":"1.0.0",
      #Unique path to the project to ensure paralell builds
      "projectPath":"D:\\wkspaces\\SimpleUnityProject_Dev",
      #Static method to execute inside of the project. You may parse build args here
      "executeMethod":"Editor.Builder.BuildCommand.ExecuteBuild",
      #Build output directory
      "buildDirectory":"E:\\OneDrive - PXFD\\Builds\\SimpleUnityProject\\Dev",
      #Target platform
      "buildTarget":"Android",
      #Target environment, passed as argument
      "env":"Development",
      #Script to call before build, to pull the latest version of the game
      "updateProjectScript":"scripts\\update_workspace_git.ps1",
      #Script to call after build, to upload generated addressable assets,
      "postBuildScript":"scripts\\upload_addressables.ps1",
      #A Json of build reports will be sent to this URL. Perfect for Slack messages
      "webhookUrl":"Slack/ Discord URL",
      #This is a special script, necessary for iOS builds, handling the xcode build phase
      "xcodeScript":"scripts/build_xcode.ps1"
   }
```
Every entry of the configuration will be **passed as arguments** as well into unity.

It is possible to override most of these by committing a `BuildSettings.txt` file into the project root. The build server will **prioritize its content** over the projects config file. Example of BuildSettings.txt:
```
{  
   "engineVersion":"2018.2.14f1",
   "projectVersion":"1.1.2",
   "executeMethod":"Editor.Builder.BuildCommand.ExecuteBuild"
}
```
*After the build server pulls the latest version of this file, it will use the values of the `engineVersion`, `projectVersion` and `executeMethod` to build the project*

## iOS Build
Is working on the `apple_system` branch. Will build your app and upload it straight to TestFlight. This makes it possible to build iOS from any platform.

You'll need the following things to make it work:
- Download your provisioning licence file and name it "ios.mobileprovision" to your project root
    - Get it from here: https://developer.apple.com/account/ios/profile/
- Import the xcode manipulation script to your  unity project
    - Is in this repo, in the `unity_plugins` folder, called `XcodeBuildPostProcessor`
- Unity Team Id: `HFN7ALEN9T` to build settings
- A build configuration with `iOS` target
