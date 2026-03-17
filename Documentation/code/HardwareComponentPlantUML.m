@startuml
node PC {
    Component [Server] {
        [AI Model\n(YOLOv5)]
        interface "Control Monitor\n(GUI)" as GUI
    }
    Component Network {
        interface "DNS Service"
        interface "Wi-Fi Hotspot"
    }
    Component "Display Monitor" as monitor {
    }
    
    GUI --> monitor
}

node "KUKA Robot" {
    Component "KR C2"
    Component [Robot Arm] as Robot
    node "Grabber" {
        node "Raspberry Pi" as Rpi {
            Component Camera
        }
        Component Battery
        interface Driver
        Component "Servo Motor" as motor
    }
    
    "KR C2" <-> Robot: Information Highway
    Rpi -> Driver: via GPIO
    Driver -> motor
    Battery --> Driver
}

Actor user

Server ....> "KR C2": Ethernet/IP\nvia DNS Service

user --> monitor: via mouse

Server <....> Rpi: Wi-Fi via Hotspot
@enduml