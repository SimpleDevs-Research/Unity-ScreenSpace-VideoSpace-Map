using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class ToggleMenu : MonoBehaviour
{
    public GameObject menuObject = null;

    public void Toggle() {
        if (menuObject != null) menuObject.SetActive(!menuObject.activeInHierarchy);
    }
}
