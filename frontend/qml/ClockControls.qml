import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

RowLayout {
    id: clockControls
    spacing: 8
    
    property var screen
    
    Button {
        text: "Set Alarm"
        Layout.preferredWidth: 120
        Layout.preferredHeight: 36
        onClicked: console.log("Set alarm clicked")
    }
    
    Button {
        text: "Timer"
        Layout.preferredWidth: 120
        Layout.preferredHeight: 36
        onClicked: console.log("Timer clicked")
    }
    
    Button {
        text: "Stopwatch"
        Layout.preferredWidth: 120
        Layout.preferredHeight: 36
        onClicked: console.log("Stopwatch clicked")
    }
} 