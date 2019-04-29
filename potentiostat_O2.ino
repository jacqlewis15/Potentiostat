// order of operations:
// - start arduino (by plugging in)
// - start potentiostat cycling (on UI)
// - at some point cycles stop on potentiostat (by hand/auto)
// - at this point, either separate code run by hand to talk to
//   the arduino or at end of script (by hand first)
// - arduino writes data to serial port and computer saves it as
//   text file
// - unplug arduino


// computer tells arduino through serial port to send info
// arduino stops measuring oxygen and sends data
// computer reads data and writes text file


const int O2pin = A0;
double calibration = 228.0;
const int len = 1000;
float O2val[len];
int j = 0;
int maxJ = 0;

bool sending = false;
bool collecting = true;
String bitIn;

void initFloatArray( float arr[], int arraySize) {
  for (int i = 0; i<arraySize; i++) {
    arr[i] = 0.0;
  }
}

int calibrate() {
  long sum = 0;
  for(int i=0; i<64; i++)
  {
    sum += analogRead(O2pin);
  }
  sum >>= 6;
  return sum;
}

void setup() {
  Serial.begin(9600);
  initFloatArray(O2val, len);
}

float readO2Vout() {
  long sum = 0;
  for(int i=0; i<64; i++)
  {
    sum += analogRead(O2pin);
  }
  sum >>= 6;
  float MeasuredVout = sum / calibration;
  return MeasuredVout;
}

float readConcentration() {
  // Vout samples are with reference to 5V
  float MeasuredVout = readO2Vout();
  float Concentration = MeasuredVout * 0.209;
  float Concentration_Percentage=Concentration*100;
  return Concentration_Percentage;
}

void loop() {
  if (Serial.available() > 0) {
    bitIn = Serial.readString();
    if (bitIn == "start") {
      collecting = true;
      sending = false;
      j = 0;
      maxJ = 0;
      initFloatArray(O2val, len);
    }
    else if (bitIn == "send") {
      collecting = false;
      sending = true;
      maxJ = j;
      j = 0;
      Serial.println(maxJ);
    }
  }
  if (collecting) {
    // read sensor
    O2val[j] = readConcentration();
    j ++;
    delay(3000);
  }
  else if (sending && j < maxJ) {
    // print data structure to serial port
    Serial.println(O2val[j]);
    j ++;
    delay(100);
  }
}
