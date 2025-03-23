import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

RowLayout {
    id: photoControls
    spacing: 8
    
    property var screen
    
    Button {
        text: "Upload"
        Layout.preferredWidth: 120
        Layout.preferredHeight: 36
        onClicked: console.log("Upload clicked")
    }
    
    Button {
        text: "Slideshow"
        Layout.preferredWidth: 120
        Layout.preferredHeight: 36
        onClicked: console.log("Slideshow clicked")
    }
    
    Button {
        text: "Edit"
        Layout.preferredWidth: 120
        Layout.preferredHeight: 36
        onClicked: console.log("Edit clicked")
    }
} 