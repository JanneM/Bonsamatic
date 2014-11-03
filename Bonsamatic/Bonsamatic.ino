// Bonsamatic sketch with time setting and analog output display
//
// Copyright 2014 Jan Moren
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
// 
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
// 
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>.


#define DEBUG false

// We put the lookup table in PROGMEM to save RAM memory space
#include <avr/pgmspace.h>

// cumulative time left in seconds for a given value of output.
// generated as tleft in analogdisplay.py
const prog_uint32_t tleft[] PROGMEM = {
      0,    823,   1659,   2508,   3370,   4246,   5137,   6041,
   6959,   7893,   8841,   9804,  10782,  11776,  12786,  13811,
  14853,  15912,  16987,  18079,  19189,  20316,  21462,  22625,
  23807,  25007,  26227,  27466,  28725,  30003,  31302,  32622,
  33962,  35324,  36708,  38113,  39541,  40991,  42464,  43961,
  45481,  47026,  48595,  50189,  51808,  53453,  55125,  56822,
  58547,  60299,  62457,  65385,  68329,  71290,  74265,  77256,
  80262,  83283,  86319,  89370,  92434,  95513,  98606, 101713,
 104834, 107968, 111116, 114276, 117450, 120637, 123837, 127050,
 130275, 133512, 136762, 140024, 143298, 146584, 149882, 153192,
 156514, 159847, 163191, 166547, 169914, 173292, 176681, 180081,
 183492, 186914, 190346, 193789, 197243, 200707, 204181, 207666,
 211160, 214665, 218180, 221705, 225240, 228785, 232339, 235903,
 239477, 243060, 246653, 250255, 253867, 257488, 261118, 264757,
 268405, 272062, 275729, 279404, 283088, 286781, 290483, 294194,
 297913, 301640, 305377, 309122, 312875, 316637, 320407, 324185,
 327972, 331767, 335570, 339381, 343200, 347027, 350863, 354706,
 358557, 362416, 366283, 370157, 374040, 377930, 381828, 385733,
 389646, 393566, 397494, 401430, 405373, 409323, 413281, 417246,
 421218, 425198, 429184, 433178, 437179, 441188, 445203, 449225,
 453255, 457291, 461335, 465385, 469442, 473506, 477577, 481655,
 485740, 489831, 493929, 498034, 502145, 506263, 510388, 514519,
 518657, 522801, 526952, 531109, 535273, 539443, 543619, 547802,
 551992, 556187, 560389, 564597, 568812, 573032, 577259, 581492,
 585731, 589977, 594228, 598486, 602749, 607019, 611294, 615576,
 619864, 624157, 628457, 632762, 637073, 641390, 645713, 650042,
 654377, 658717, 663064, 667415, 671773, 676136, 680506, 684880,
 689261, 693647, 698038, 702436, 706838, 711247, 715661, 720080,
 724505, 728935, 733371, 737813, 742259, 746711, 751169, 755632,
 760100, 764574, 769053, 773537, 778027, 782522, 787022, 791527,
 796038, 800554, 805075, 809601, 814133, 818669, 823211, 827758,
 832310, 836867, 841429, 845996, 850569, 855146, 859728, 864316};

// The set times data structure. It's small enough that we don't bother
// putting it in progmem.

typedef struct {
  unsigned long t;    // actual time set in seconds
  int idx;            // index to closest step in tleft
} 
set_times_struct;

const int n_times = 16;

set_times_struct set_times[n_times] = {
{     0,   0},	 //   0 hours
{ 21600,  22},	 //   6 hours
{ 43200,  38},	 //  12 hours
{ 64800,  51},	 //  18 hours
{ 86400,  58},	 //  24 hours
{129600,  72},	 //  36 hours
{172800,  85},	 //  48 hours
{216000,  97},	 //  60 hours
{259200, 109},	 //  72 hours
{345600, 133},	 //  96 hours
{432000, 155},	 // 120 hours
{518400, 176},	 // 144 hours
{604800, 196},	 // 168 hours
{691200, 216},	 // 192 hours
{777600, 236},	 // 216 hours
{864000, 255}	 // 240 hours
};

// Analog display
int out_display = 9;	    // port

// light LED 
int led = 13;		    // port
unsigned long led_time;	    // counter for blink rate
int led_state;		    // on or off

// Rotary encoder
int in_A = 3;		    // port
int in_B = 2;		    // port
int last_A = HIGH;	    // hold state to determine direction

// Pump
int pump = 12;		    // port
int pumptime = 30*1000;	    // watering time; determines total water volume
unsigned long water_time;   // clock time at which we started watering
bool watering = false;	    // are we watering or not

// Mode switch
int in_run = 7;		    // port
int in_set = 8;		    // port

// timing data
unsigned long end_time;     // absolute time to start watering
unsigned long next_time;    // absolute time to take the next step down 
int cur_idx = 0;            // current voltage index: 0 <= cur_ind <= 255
int set_idx = 5;	    // set time index 0<= set_idx < n_times
// state
#define NO_STATE 0	    // turned off
#define RUN_STATE 1	    // counting down or watering
#define SET_STATE 2	    // setting the time
char mode = NO_STATE;

//
// functions
//
  
void setup() {

  // Set up all ports
  if (DEBUG) Serial.begin(9600);
  pinMode(in_A, INPUT);
  pinMode(in_B, INPUT);
  pinMode(in_run, INPUT);
  pinMode(in_set, INPUT);
  pinMode(led, OUTPUT);
  pinMode(pump, OUTPUT);

  start_countdown();

  // set the led blink state
  led_time = millis();
  led_state = HIGH;
}

// translate from seconds to milliseconds.
// also useful for debugging.
inline unsigned long s_to_ms(unsigned long sec) {
  return sec*1000;
}

// read a tleft table index from PROGMEM
inline unsigned long read_tleft(int idx) {
  return s_to_ms(pgm_read_dword_near(tleft+idx));  
}

// fix the watering time and set the initial index time
void start_countdown() {

  if (DEBUG) Serial.print("start countdown: ");
  
  unsigned long get_time = millis();
  cur_idx = set_times[set_idx].idx;

  // now + the total waiting time = when we should water.
  end_time = get_time+s_to_ms(set_times[set_idx].t);
  unsigned long nt = read_tleft(cur_idx);

  // when do we next step down the analog counter?
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
  
  // set the display to the current value
  analogWrite(out_display, cur_idx);   
}  

// we start the watering procedure
void start_water() {

  if (DEBUG) Serial.print("start water: ");
  
  // now + pumptime = when to stop the pump
  water_time = millis() + pumptime;
  
  if (DEBUG) Serial.print(water_time);
  if (DEBUG) Serial.print ("\n");
  
  // start pumping
  digitalWrite(pump, HIGH); 
  watering = true;
}  
 
// stop the water and restart the countdown from the beginning
void stop_water() {

  if (DEBUG) Serial.print("stop water\n");

  digitalWrite(pump, LOW);
  watering = false; 
  start_countdown();
} 

// Check if it's time to stop the water yet
void do_water() {

  unsigned long get_time = millis();
  if (get_time > water_time) {
    stop_water();
  }
}

// the main countdown procedure, called in a loop
void do_countdown() {

  // We start watering once the clock time passes the end time 
  // we set at the start_countdown
  unsigned long get_time = millis();
  if (get_time >= end_time) {
    start_water();    
  } 

  // if we surpass the time to step down the counter, we do so, and 
  // figure out the time to step it down the next time in turn.
  else if (get_time >= next_time) {
    cur_idx--;
    unsigned long nt = read_tleft(cur_idx);
    next_time = end_time-nt;
    analogWrite(out_display, cur_idx);   
  }  
}

// when setting the time, keep the time index in the valid range, and set the
// dial to reflect the current choice.
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

  // we're setting the time
  if (mode==SET_STATE) {
    do_set_time();
  }

  // we're counting down or watering
  if (mode==RUN_STATE) {
    if (watering == false) {
      do_countdown();		
    } else {
      do_water();	    
    }
  }
  
  delay(1);

  // we read the state of the set switch and determine if
  // we're setting the time, running, or are turned off.
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

