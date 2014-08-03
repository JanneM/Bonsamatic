// Bonsamatic with time setting and analog output display
//
// Jan Moren

#define DEBUG false

// lookup tables
#include <avr/pgmspace.h>

// cumulative time left in seconds for a given value of output.
// generated as tleft in analogdisplay.py
const prog_uint32_t tleft[] PROGMEM = {
  0,    822,   1658,   2507,   3370,   4246,   5136,   6040,
  6959,   7892,   8840,   9803,  10782,  11776,  12785,  13811,
  14853,  15911,  16987,  18079,  19189,  20316,  21461,  22625,
  23806,  25007,  26227,  27466,  28724,  30003,  31302,  32621,
  33962,  35324,  36707,  38112,  39540,  40990,  42464,  43960,
  45481,  47026,  48595,  50189,  51808,  53453,  55124,  56822,
  58546,  60298,  62456,  65385,  68329,  71289,  74265,  77256,
  80262,  83283,  86319,  89369,  92434,  95513,  98606, 101713,
  104833, 107968, 111115, 114276, 117450, 120637, 123837, 127049,
  130274, 133512, 136762, 140024, 143298, 146584, 149882, 153192,
  156513, 159846, 163190, 166546, 169913, 173291, 176680, 180080,
  183491, 186913, 190346, 193789, 197242, 200706, 204181, 207665,
  211160, 214665, 218180, 221705, 225240, 228784, 232339, 235903,
  239477, 243060, 246653, 250255, 253866, 257487, 261117, 264756,
  268405, 272062, 275728, 279404, 283088, 286781, 290483, 294193,
  297912, 301640, 305376, 309121, 312874, 316636, 320406, 324185,
  327971, 331766, 335569, 339380, 343200, 347027, 350862, 354705,
  358556, 362415, 366282, 370157, 374039, 377929, 381827, 385732,
  389645, 393566, 397494, 401429, 405372, 409323, 413280, 417245,
  421218, 425197, 429184, 433178, 437179, 441187, 445203, 449225,
  453254, 457291, 461334, 465385, 469442, 473506, 477577, 481655,
  485739, 489830, 493928, 498033, 502144, 506262, 510387, 514518,
  518656, 522800, 526951, 531108, 535272, 539442, 543619, 547802,
  551991, 556187, 560389, 564597, 568811, 573032, 577259, 581492,
  585731, 589976, 594228, 598485, 602749, 607018, 611294, 615575,
  619863, 624157, 628456, 632761, 637073, 641390, 645713, 650042,
  654376, 658717, 663063, 667415, 671773, 676136, 680505, 684880,
  689260, 693646, 698038, 702435, 706838, 711246, 715660, 720080,
  724504, 728935, 733371, 737812, 742259, 746711, 751169, 755632,
  760100, 764574, 769053, 773537, 778026, 782521, 787022, 791527,
  796038, 800553, 805075, 809601, 814132, 818669, 823211, 827757,
  832309, 836866, 841429, 845996, 850568, 855145, 859728, 864315};

typedef struct {
  unsigned long t;    // actual time set in seconds
  int idx;            // index to closest step in tleft
} 
set_times_struct;

const int n_times = 16;

set_times_struct set_times[n_times] = {
  {0     , 0  },   // 0 hours
  {21600 , 22 },   // 6 hours
  {43200 , 38 },   // 12 hours
  {64800 , 51 },   // 18 hours
  {86400 , 58 },   // 24 hours
  {129600, 72 },   // 36 hours
  {172800, 85 },   // 48 hours
  {216000, 97 },   // 60 hours
  {259200, 109},   // 72 hours
  {345600, 133},   // 96 hours
  {432000, 155},   // 120 hours
  {518400, 176},   // 144 hours
  {604800, 196},   // 168 hours
  {691200, 216},   // 192 hours
  {777600, 236},   // 216 hours
  {864000, 255}    // 240 hours
};

// Analog display
int out_display = 9;
int voltage = 0;

int led = 13;
unsigned long led_time;
int led_state;
// Rotary encoder
int in_A = 3;
int in_B = 2;
int last_A = HIGH;

// Pump
int pump = 12;
int pumptime = 20*1000;
unsigned long water_time;
bool watering = false;

// Mode switch
int in_run = 7;
int in_set = 8;

// timing data
unsigned long end_time;     // absolute time at which the countdown is finished and we start watering
unsigned long next_time;    // absolute time at which we take the next countdown step down 
int cur_idx = 0;            // current position index: 0 <= cur_ind <= 255
int set_idx = 5; // set time position 0<= set_idx < n_times
// state
#define NO_STATE 0
#define RUN_STATE 1
#define SET_STATE 2
char mode = NO_STATE;

//
// functions
//
  
void setup() {

  // Rotary encoder set-up
  if (DEBUG) Serial.begin(9600);
  pinMode(in_A, INPUT);
  pinMode(in_B, INPUT);
  pinMode(in_run, INPUT);
  pinMode(in_set, INPUT);
  pinMode(led, OUTPUT);
  pinMode(pump, OUTPUT);
  start_countdown();
  led_time = millis();
  led_state = HIGH;
}

// translate from seconds to milliseconds.
// also useful for debugging; set
inline unsigned long s_to_ms(unsigned long sec) {
  return sec/10;
}

inline unsigned long read_tleft(int idx) {
  return s_to_ms(pgm_read_dword_near(tleft+idx));  
}

// fix our chosen time and set the initial index time
void start_countdown() {
  if (DEBUG) Serial.print("start countdown: ");
  unsigned long get_time = millis();
  cur_idx = set_times[set_idx].idx;
  end_time = get_time+s_to_ms(set_times[set_idx].t);
  unsigned long nt = read_tleft(cur_idx);
  next_time = end_time-nt;  
  if (next_time > get_time) 
    next_time = get_time;
  if (DEBUG) {
    Serial.print(end_time);
    Serial.print(" - ");  
    Serial.print(nt);
    Serial.print(" = ");
    Serial.print(next_time);
    Serial.print("\n");
  }

  analogWrite(out_display, cur_idx);   
}  

void start_water() {
  if (DEBUG) Serial.print("start water: ");
  water_time = millis() + pumptime;
  if (DEBUG) Serial.print(water_time);
  if (DEBUG) Serial.print ("\n");
  digitalWrite(pump, HIGH); 
   watering = true;
}  
 
void stop_water() {
  if (DEBUG) Serial.print("stop water\n");
  digitalWrite(pump, LOW);
  watering = false; 
  start_countdown();
} 

void do_water() {  
  unsigned long get_time = millis();
  if (get_time > water_time) {
    stop_water();
  }
}

void do_countdown() {

//  Serial.print("Do countdown\n");

  unsigned long get_time = millis();
  if (get_time >= end_time) {
    start_water();    
  } 
  else if (get_time >= next_time) {
    cur_idx--;
    unsigned long nt = read_tleft(cur_idx);
    next_time = end_time-nt;
    analogWrite(out_display, cur_idx);   
  }  
}

// keep the time index in the valid range, and set the dial to 
// reflect the current choice.
int set_time(int sidx) {

  if (sidx < 0) {
    sidx = 0;
  }
  if (sidx >= n_times) {
    sidx = n_times-1;
  }

  analogWrite(out_display, set_times[sidx].idx);
  return sidx;
}

// Blink the LED while we're in the time set mode
void set_led() {

  unsigned long now_time = millis();

  if ((led_time + 500UL) < now_time) {

    if (led_state == HIGH) {
      led_state = LOW;
    } else {
      led_state = HIGH;
    } 
    led_time = now_time;
  }    
  digitalWrite(led, led_state);
}

// check the state of the rotary dial and set the desired time based on that.
void do_set_time() {
  int A_state = digitalRead(in_A);

  if ((last_A == HIGH) && (A_state == LOW)) {
    int B_state = digitalRead(in_B);

    if (B_state == HIGH) {            // clockwise
      set_idx = set_time(set_idx+1);
    } 
    else {                            // counterclockwise
      set_idx = set_time(set_idx-1);
    }
  }
  last_A = A_state;
  set_led();  
}  

void loop() {

  if (mode==SET_STATE) {
    do_set_time();
  }

  if (mode==RUN_STATE) {
    if (watering == false) {
      do_countdown();
    } else {
      do_water();
    }
  }
  
  delay(1);

  int set_switch = digitalRead(in_set);
  int run_switch = digitalRead(in_run);

// Set the time

  if (set_switch == HIGH) {
    if (mode != SET_STATE) {
      mode = SET_STATE;
      led_time = millis();
      led_state = HIGH;
      stop_water();
    }
  }

// Run the countdown

  if (run_switch == HIGH) {
    if (mode != RUN_STATE) {
      mode = RUN_STATE;
      start_countdown();
      digitalWrite(led,HIGH);
    }
  }

// Turn off.

  if ((run_switch == LOW) && (set_switch == LOW)) {
    if (mode != NO_STATE) {
      mode = NO_STATE;
      digitalWrite(led, LOW);
      stop_water();
    }
  }
}






