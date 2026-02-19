// NeuroVision - Home Appliance Controller
// Firmware for Arduino UNO
// Receives serial commands from Python and toggles outputs accordingly

// Pin definitions
const int RED_PIN    = 2;
const int YELLOW_PIN = 3;
const int BLUE_PIN   = 4;
const int WHITE_PIN  = 5;

// State variables
bool red_state    = false;
bool yellow_state = false;
bool blue_state   = false;
bool white_state  = false;

String inputBuffer = "";

void setup() {
  Serial.begin(9600);

  pinMode(RED_PIN,    OUTPUT);
  pinMode(YELLOW_PIN, OUTPUT);
  pinMode(BLUE_PIN,   OUTPUT);
  pinMode(WHITE_PIN,  OUTPUT);

  digitalWrite(RED_PIN,    LOW);
  digitalWrite(YELLOW_PIN, LOW);
  digitalWrite(BLUE_PIN,   LOW);
  digitalWrite(WHITE_PIN,  LOW);

  Serial.println("NeuroVision Ready");
}

void loop() {
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\n') {
      processCommand(inputBuffer);
      inputBuffer = "";
    } else {
      inputBuffer += c;
    }
  }
}

void processCommand(String cmd) {
  cmd.trim();
  cmd.toUpperCase();

  if (cmd == "RED_TOGGLE") {
    red_state = !red_state;
    digitalWrite(RED_PIN, red_state ? HIGH : LOW);
    Serial.println(red_state ? "RED ON" : "RED OFF");
  }
  else if (cmd == "YELLOW_TOGGLE") {
    yellow_state = !yellow_state;
    digitalWrite(YELLOW_PIN, yellow_state ? HIGH : LOW);
    Serial.println(yellow_state ? "YELLOW ON" : "YELLOW OFF");
  }
  else if (cmd == "BLUE_TOGGLE") {
    blue_state = !blue_state;
    digitalWrite(BLUE_PIN, blue_state ? HIGH : LOW);
    Serial.println(blue_state ? "BLUE ON" : "BLUE OFF");
  }
  else if (cmd == "WHITE_TOGGLE") {
    white_state = !white_state;
    digitalWrite(WHITE_PIN, white_state ? HIGH : LOW);
    Serial.println(white_state ? "WHITE ON" : "WHITE OFF");
  }
}
