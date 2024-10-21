# Classic Load Balancer to ELB Synchronization

## Projektbeschreibung

Dieses Projekt wurde entwickelt, um die registrierten Instanzen eines Classic Load Balancers (CLB) mit den registrierten Instanzen einer ELB Target Group zu synchronisieren. Die Lambda-Funktion überprüft die registrierten Instanzen in beiden Gruppen und synchronisiert sie, indem sie fehlende Instanzen registriert und überflüssige Instanzen deregistriert.

## Voraussetzungen

- Python 3.x installiert
- `pip` installiert (Python Package Manager)

## Einrichtung

### 1. Virtuelle Umgebung erstellen

Es wird empfohlen, eine virtuelle Umgebung zu erstellen, um Abhängigkeiten isoliert zu verwalten.

- Öffne ein Terminal und navigiere in das Projektverzeichnis.
- Erstelle eine virtuelle Umgebung mit folgendem Befehl:

  ```bash
  python -m venv venv
  ```
- Aktiviere die virtuelle Umgebung (für Apfel-Jünger):

    ```bash
    source venv/bin/activate
    ```

### 2. Abhängigkeiten installieren

Installiere die erforderlichen Abhängigkeiten mit dem folgenden Befehl:

```bash
pip install -r requirements.txt
```

### 3. Tests ausführen

Das Projekt enthält Unit-Tests, die mit pytest geschrieben wurden. Diese Tests befinden sich in der Datei test_classic_lb_to_elb.py und testen die Synchronisation zwischen dem CLB und der ELB Target Group.

Um die Tests auszuführen, führe den folgenden Befehl aus:

```bash
pytest test_classic_lb_to_elb.py
```

Die Tests werden in der Konsole ausgeführt, und das Ergebnis wird angezeigt. pytest führt die Tests automatisch und zeigt an, ob alle Tests erfolgreich waren oder ob Fehler aufgetreten sind.

#### Hinweis:
Das Projekt verwendet moto, um AWS-Dienste in einer Mocking-Umgebung zu simulieren. Dies verhindert, dass echte AWS-Ressourcen während der Tests belastet werden.