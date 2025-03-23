import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

RowLayout {
    id: calendarControls
    spacing: 8
    
    property var screen
    
    Button {
        text: "Add Event"
        Layout.preferredWidth: 120
        Layout.preferredHeight: 36
        onClicked: console.log("Add event clicked")
    }
    
    Button {
        text: "View Month"
        Layout.preferredWidth: 120
        Layout.preferredHeight: 36
        onClicked: console.log("View month clicked")
    }
    
    Button {
        text: "Sync"
        Layout.preferredWidth: 120
        Layout.preferredHeight: 36
        onClicked: console.log("Sync clicked")
    }
} 