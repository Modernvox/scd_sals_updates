; ------------------------------------------------------------
; DoubleClickCopy.ahk  (for AutoHotkey v1.1.37)
;------------------------------------------------------------

~LButton::
if (A_PriorHotkey = "~LButton" && A_TimeSincePriorHotkey < 300)
{
    Sleep 50
    Send ^c
}
return
myrna
kamrein
shanasim62944