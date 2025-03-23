import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

// Controls component for Chat Screen
RowLayout {
    id: chatControls
    spacing: 10
    
    // Reference to the screen this controls
    property var screen
    
    // Force alignment to left
    Layout.alignment: Qt.AlignLeft
    
    Button {
        id: sttButton
        property bool isListening: false
        Layout.preferredWidth: 50
        Layout.preferredHeight: 40
        background: Rectangle {
            color: "transparent"
            radius: 5
        }
        onClicked: {
            isListening = !isListening
            screen.chatLogic.toggleSTT()
        }
        
        Image {
            anchors.centerIn: parent
            source: sttButton.isListening ? "../icons/stt_on.svg" : "../icons/stt_off.svg"
            width: 24
            height: 24
            sourceSize.width: 24
            sourceSize.height: 24
        }
        
        ToolTip.visible: hovered
        ToolTip.text: isListening ? "STT On" : "STT Off"
    }
    
    Button {
        id: ttsButton
        property bool isEnabled: false
        Layout.preferredWidth: 50
        Layout.preferredHeight: 40
        background: Rectangle {
            color: "transparent"
            radius: 5
        }
        onClicked: {
            isEnabled = !isEnabled
            screen.chatLogic.toggleTTS()
        }
        
        Image {
            anchors.centerIn: parent
            source: ttsButton.isEnabled ? "../icons/sound_on.svg" : "../icons/sound_off.svg"
            width: 24
            height: 24
            sourceSize.width: 24
            sourceSize.height: 24
        }
        
        ToolTip.visible: hovered
        ToolTip.text: isEnabled ? "TTS On" : "TTS Off"
    }
    
    Button {
        id: stopButton
        Layout.preferredWidth: 50
        Layout.preferredHeight: 40
        background: Rectangle {
            color: "transparent"
            radius: 5
        }
        onClicked: screen.chatLogic.stopAll()
        
        Image {
            anchors.centerIn: parent
            source: "../icons/stop_all.svg"
            width: 24
            height: 24
            sourceSize.width: 24
            sourceSize.height: 24
        }
        
        ToolTip.visible: hovered
        ToolTip.text: "Stop"
    }
    
    Button {
        id: clearButton
        Layout.preferredWidth: 50
        Layout.preferredHeight: 40
        background: Rectangle {
            color: "transparent"
            radius: 5
        }
        onClicked: {
            screen.chatLogic.clearChat()
            screen.chatModel.clear()
        }
        
        Image {
            anchors.centerIn: parent
            source: "../icons/clear_all.svg"
            width: 24
            height: 24
            sourceSize.width: 24
            sourceSize.height: 24
        }
        
        ToolTip.visible: hovered
        ToolTip.text: "Clear"
    }
    
    // Add a spacer to prevent stretching
    Item {
        Layout.fillWidth: true
    }

    // Connect signals from ChatLogic to update button states
    Connections {
        target: screen ? screen.chatLogic : null
        
        function onSttStateChanged(enabled) {
            sttButton.isListening = enabled
        }
        
        function onTtsStateChanged(enabled) {
            ttsButton.isEnabled = enabled
        }
    }
} 