import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

RowLayout {
    id: weatherControls
    spacing: 8
    
    property var screen
    
    Button {
        text: "Update Weather"
        Layout.preferredWidth: 120
        Layout.preferredHeight: 36
        onClicked: console.log("Update weather clicked")
    }
    
    Button {
        text: "Change Location"
        Layout.preferredWidth: 120
        Layout.preferredHeight: 36
        onClicked: console.log("Change location clicked")
    }
    
    Button {
        text: "Forecast"
        Layout.preferredWidth: 120
        Layout.preferredHeight: 36
        onClicked: console.log("Forecast clicked")
    }
} 