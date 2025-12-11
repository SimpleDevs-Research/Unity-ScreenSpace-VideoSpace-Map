using UnityEngine;
using Helpers;

public class WriteLog : MonoBehaviour
{
    
    public string dirName = "";

    string filename = "";
    string myLog = "*begin log";
    int kChars = 700;

    void OnEnable() { 
        // Prep dirname
        string dname = $"{Application.persistentDataPath}/{Helpers.SaveSystemMethods.GetCurrentDateTime()}";
        if (dirName != null && dirName.Length > 0) {
            dname = $"{Application.persistentDataPath}/{dirName}";
        }
        Helpers.SaveSystemMethods.CheckOrCreateDirectory(dname);

        // Prep filename
        string r = Random.Range(1000, 9999).ToString();
        filename = dname + "/log-" + r + ".txt";

        // Add listener to log meessager
        Application.logMessageReceived += Log; 
    }
    
    void OnDisable() { 
        Application.logMessageReceived -= Log; 
    }

    
    public void Log(string logString, string stackTrace, LogType type)
    {
       // for onscreen...
        myLog = myLog + " " + logString;
        if (myLog.Length > kChars) { 
            myLog = myLog.Substring(myLog.Length - kChars); 
        }

        try { System.IO.File.AppendAllText(filename, logString + "\n"); }
        catch { }
    }

}