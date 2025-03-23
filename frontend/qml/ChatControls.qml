import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

// Controls component for Chat Screen
RowLayout {
    id: chatControls
    spacing: 8
    
    // Reference to the screen this controls
    property var screen
    
    Button {
        id: sttButton
        text: "STT Off"
        property bool isListening: false
        Layout.preferredWidth: 120
        Layout.preferredHeight: 40
        onClicked: {
            isListening = !isListening
            text = isListening ? "STT On" : "STT Off"
            screen.chatLogic.toggleSTT()
        }
    }
    
    Button {
        id: ttsButton
        text: "TTS Off"
        property bool isEnabled: false
        Layout.preferredWidth: 120
        Layout.preferredHeight: 40
        onClicked: {
            isEnabled = !isEnabled
            text = isEnabled ? "TTS On" : "TTS Off"
            screen.chatLogic.toggleTTS()
        }
    }
    
    Button {
        id: clearButton
        text: "CLEAR"
        Layout.preferredWidth: 120
        Layout.preferredHeight: 40
        onClicked: {
            screen.chatLogic.clearChat()
            screen.chatModel.clear()
        }
    }
    
    Button {
        id: stopButton
        text: "STOP"
        Layout.preferredWidth: 120
        Layout.preferredHeight: 40
        onClicked: screen.chatLogic.stopAll()
    }

    // Connect signals from ChatLogic to update button states
    Connections {
        target: screen ? screen.chatLogic : null
        
        function onSttStateChanged(enabled) {
            sttButton.isListening = enabled
            sttButton.text = enabled ? "STT On" : "STT Off"
        }
        
        function onTtsStateChanged(enabled) {
            ttsButton.isEnabled = enabled
            ttsButton.text = enabled ? "TTS On" : "TTS Off"
        }
    }
} 