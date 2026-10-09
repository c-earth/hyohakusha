/*
 * @Author: ELEGOO
 * @Date: 2019-10-22 11:59:09
 * @LastEditTime: 2021-01-05 09:30:14
 * @LastEditors: Changhua
 * @Description: Smart Robot Car V4.0
 * @FilePath: 
 */
#include <avr/wdt.h>
//#include <hardwareSerial.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "ApplicationFunctionSet_xxx0.h"
#include "DeviceDriverSet_xxx0.h"

#include "ArduinoJson-v6.11.1.h" //ArduinoJson
#include "MPU6050_getdata.h"

#define _is_print 1
#define _Test_print 0

ApplicationFunctionSet Application_FunctionSet;

/*Hardware device object list*/
MPU6050_getdata AppMPU6050getdata;
DeviceDriverSet_RBGLED AppRBG_LED;
DeviceDriverSet_Key AppKey;
DeviceDriverSet_ITR20001 AppITR20001;
DeviceDriverSet_Voltage AppVoltage;

DeviceDriverSet_Motor AppMotor;
DeviceDriverSet_ULTRASONIC AppULTRASONIC;
DeviceDriverSet_Servo AppServo;
/*f(x) int */
static boolean
function_xxx(long x, long s, long e) //f(x)
{
  if (s <= x && x <= e)
    return true;
  else
    return false;
}
static void
delay_xxx(uint16_t _ms)
{
  wdt_reset();
  for (unsigned long i = 0; i < _ms; i++)
  {
    delay(1);
  }
}

/*Movement Direction Control List*/
enum SmartRobotCarMotionControl
{
  Forward,       //(1)
  Backward,      //(2)
  Left,          //(3)
  Right,         //(4)
  LeftForward,   //(5)
  LeftBackward,  //(6)
  RightForward,  //(7)
  RightBackward, //(8)
  stop_it        //(9)
};               //direction方向:（1）、（2）、 （3）、（4）、（5）、（6）

/*Mode Control List*/
enum SmartRobotCarFunctionalModel
{
  Standby_mode,           /*Standby Mode*/
  CMD_inspect = 5,
  CMD_Programming_mode,                   /*Programming Mode*/
  CMD_ClearAllFunctions_Standby_mode,     /*Clear All Functions And Enter Standby Mode*/
  CMD_CarControl_TimeLimit = 10,               /*Car Movement Direction Control With Time Limit*/
  CMD_ServoControl = 13,                       /*Servo Motor Control*/

};

/*Application Management list*/
struct Application_xxx
{
  SmartRobotCarMotionControl Motion_Control;
  SmartRobotCarFunctionalModel Functional_Mode;
  unsigned long CMD_CarControl_Millis;
};
Application_xxx Application_SmartRobotCarxxx0;

void ApplicationFunctionSet_SmartRobotCarMotionControl(SmartRobotCarMotionControl direction, uint8_t is_speed);

void ApplicationFunctionSet::ApplicationFunctionSet_Init(void)
{
  bool res_error = true;
  Serial.begin(9600);
  AppVoltage.DeviceDriverSet_Voltage_Init();
  AppMotor.DeviceDriverSet_Motor_Init();
  AppServo.DeviceDriverSet_Servo_Init(90);
  AppKey.DeviceDriverSet_Key_Init();
  AppRBG_LED.DeviceDriverSet_RBGLED_Init(20);
  AppULTRASONIC.DeviceDriverSet_ULTRASONIC_Init();
  AppITR20001.DeviceDriverSet_ITR20001_Init();
  res_error = AppMPU6050getdata.MPU6050_dveInit();
  AppMPU6050getdata.MPU6050_calibration();

  // while (Serial.read() >= 0)
  // {
  //   /*Clear serial port buffer...*/
  // }
  Application_SmartRobotCarxxx0.Functional_Mode = Standby_mode;
}

/*
  Movement Direction Control:
  Input parameters:     1# direction:Forward（1）、Backward（2）、 Left（3）、Right（4）、LeftForward（5）、LeftBackward（6）、RightForward（7）RightBackward（8）
                        2# speed(0--255)
*/
static void ApplicationFunctionSet_SmartRobotCarMotionControl(SmartRobotCarMotionControl direction, uint8_t is_speed)
{
  uint8_t speed = is_speed;
  switch (direction)
  {
  case /* constant-expression */
      Forward:
    /* code */
    AppMotor.DeviceDriverSet_Motor_control(direction_just, speed, direction_just, speed, control_enable);

    break;
  case /* constant-expression */ Backward:
    /* code */
    AppMotor.DeviceDriverSet_Motor_control(direction_back, speed, direction_back, speed, control_enable);

    break;
  case /* constant-expression */ Left:
    /* code */
    AppMotor.DeviceDriverSet_Motor_control(/*direction_A*/ direction_just, /*speed_A*/ speed,
                                           /*direction_B*/ direction_back, /*speed_B*/ speed, /*controlED*/ control_enable); //Motor control
    break;
  case /* constant-expression */ Right:
    /* code */
    AppMotor.DeviceDriverSet_Motor_control(/*direction_A*/ direction_back, /*speed_A*/ speed,
                                           /*direction_B*/ direction_just, /*speed_B*/ speed, /*controlED*/ control_enable); //Motor control
    break;
  case /* constant-expression */ LeftForward:
    /* code */
    AppMotor.DeviceDriverSet_Motor_control(/*direction_A*/ direction_just, /*speed_A*/ speed,
                                           /*direction_B*/ direction_just, /*speed_B*/ speed / 2, /*controlED*/ control_enable); //Motor control
    break;
  case /* constant-expression */ LeftBackward:
    /* code */
    AppMotor.DeviceDriverSet_Motor_control(/*direction_A*/ direction_back, /*speed_A*/ speed,
                                           /*direction_B*/ direction_back, /*speed_B*/ speed / 2, /*controlED*/ control_enable); //Motor control
    break;
  case /* constant-expression */ RightForward:
    /* code */
    AppMotor.DeviceDriverSet_Motor_control(/*direction_A*/ direction_just, /*speed_A*/ speed / 2,
                                           /*direction_B*/ direction_just, /*speed_B*/ speed, /*controlED*/ control_enable); //Motor control
    break;
  case /* constant-expression */ RightBackward:
    /* code */
    AppMotor.DeviceDriverSet_Motor_control(/*direction_A*/ direction_back, /*speed_A*/ speed / 2,
                                           /*direction_B*/ direction_back, /*speed_B*/ speed, /*controlED*/ control_enable); //Motor control
    break;
  case /* constant-expression */ stop_it:
    /* code */
    AppMotor.DeviceDriverSet_Motor_control(/*direction_A*/ direction_void, /*speed_A*/ 0,
                                           /*direction_B*/ direction_void, /*speed_B*/ 0, /*controlED*/ control_enable); //Motor control

    break;
  default:
    break;
  }
}
/*
 Robot car update sensors' data:Partial update (selective update)
*/
void ApplicationFunctionSet::ApplicationFunctionSet_SensorDataUpdate(void)
{

  // AppMotor.DeviceDriverSet_Motor_Test();
  { /*Battery voltage status update*/
    static unsigned long VoltageData_time = 0;
    static int VoltageData_number = 1;
    if (millis() - VoltageData_time > 10) //read and update the data per 10ms
    {
      VoltageData_time = millis();
      VoltageData_V = AppVoltage.DeviceDriverSet_Voltage_getAnalogue();
      if (VoltageData_V < VoltageDetection)
      {
        VoltageData_number++;
        if (VoltageData_number == 500) //Continuity to judge the latest voltage value multiple 
        {
          VoltageDetectionStatus = true;
          VoltageData_number = 0;
        }
      }
      else
      {
        VoltageDetectionStatus = false;
      }
    }
  }

  // { /*value updation for the ultrasonic sensor：for the Obstacle Avoidance mode*/
  //   AppULTRASONIC.DeviceDriverSet_ULTRASONIC_Get(&UltrasoundPulse_us /*out*/, 1000000UL);
  //   UltrasoundDetectionStatus = function_xxx(UltrasoundPulse_us, 0, ObstacleDetection);
  // }

  // acquire timestamp
  // static unsigned long Test_time;
  // if (millis() - Test_time > 200)
  // {
  //   Test_time = millis();
  //   //AppITR20001.DeviceDriverSet_ITR20001_Test();
  // }
}
/*
  Startup operation requirement：
*/
void ApplicationFunctionSet::ApplicationFunctionSet_Bootup(void)
{
  Application_SmartRobotCarxxx0.Functional_Mode = Standby_mode;
}

/*RBG_LED set*/
void ApplicationFunctionSet::ApplicationFunctionSet_RGB(void)
{
  static unsigned long getAnalogue_time = 0;
  FastLED.clear(true);
  if (true == VoltageDetectionStatus) //Act on low power state？
  {
    if ((millis() - getAnalogue_time) > 3000)
    {
      getAnalogue_time = millis();
    }
  }
  unsigned long temp = millis() - getAnalogue_time;
  if (function_xxx((temp), 0, 500) && VoltageDetectionStatus == true)
  {
    switch (temp)
    {
    case /* constant-expression */ 0 ... 49:
      /* code */
      AppRBG_LED.DeviceDriverSet_RBGLED_xxx(0 /*Duration*/, 2 /*Traversal_Number*/, CRGB::Red);
      break;
    case /* constant-expression */ 50 ... 99:
      /* code */
      AppRBG_LED.DeviceDriverSet_RBGLED_xxx(0 /*Duration*/, 2 /*Traversal_Number*/, CRGB::Black);
      break;
    case /* constant-expression */ 100 ... 149:
      /* code */
      AppRBG_LED.DeviceDriverSet_RBGLED_xxx(0 /*Duration*/, 2 /*Traversal_Number*/, CRGB::Red);
      break;
    case /* constant-expression */ 150 ... 199:
      /* code */
      AppRBG_LED.DeviceDriverSet_RBGLED_xxx(0 /*Duration*/, 2 /*Traversal_Number*/, CRGB::Black);
      break;
    case /* constant-expression */ 200 ... 249:
      /* code */
      AppRBG_LED.DeviceDriverSet_RBGLED_xxx(0 /*Duration*/, 2 /*Traversal_Number*/, CRGB::Red);
      break;
    case /* constant-expression */ 250 ... 299:
      /* code */
      AppRBG_LED.DeviceDriverSet_RBGLED_xxx(0 /*Duration*/, 2 /*Traversal_Number*/, CRGB::Red);
      break;
    case /* constant-expression */ 300 ... 349:
      /* code */
      AppRBG_LED.DeviceDriverSet_RBGLED_xxx(0 /*Duration*/, 2 /*Traversal_Number*/, CRGB::Black);
      break;
    case /* constant-expression */ 350 ... 399:
      /* code */
      AppRBG_LED.DeviceDriverSet_RBGLED_xxx(0 /*Duration*/, 2 /*Traversal_Number*/, CRGB::Red);
      break;
    case /* constant-expression */ 400 ... 449:
      /* code */
      AppRBG_LED.DeviceDriverSet_RBGLED_xxx(0 /*Duration*/, 2 /*Traversal_Number*/, CRGB::Black);
      break;
    case /* constant-expression */ 450 ... 499:
      /* code */
      AppRBG_LED.DeviceDriverSet_RBGLED_xxx(0 /*Duration*/, 2 /*Traversal_Number*/, CRGB::Red);
      break;
    default:
      break;
    }
  }
  else if (((function_xxx((temp), 500, 3000)) && VoltageDetectionStatus == true) || VoltageDetectionStatus == false)
  {
    switch (Application_SmartRobotCarxxx0.Functional_Mode) //Act on mode control sequence
    {
    case /* constant-expression */ Standby_mode:
      /* code */
      {
        if (VoltageDetectionStatus == true)
        {
          AppRBG_LED.DeviceDriverSet_RBGLED_xxx(0 /*Duration*/, 2 /*Traversal_Number*/, CRGB::Red);
          delay(30);
          AppRBG_LED.DeviceDriverSet_RBGLED_xxx(0 /*Duration*/, 2 /*Traversal_Number*/, CRGB::Black);
          delay(30);
        }
        else
        {
          static uint8_t setBrightness = 0;
          static boolean et = false;
          static unsigned long time = 0;

          if ((millis() - time) > 10)
          {
            time = millis();
            if (et == false)
            {
              setBrightness += 1;
              if (setBrightness == 100)
                et = true;
            }
            else if (et == true)
            {
              setBrightness -= 1;
              if (setBrightness == 0)
                et = false;
            }
          }
          // AppRBG_LED.leds[1] = CRGB::Blue;
          AppRBG_LED.leds[0] = CRGB::Violet;
          FastLED.setBrightness(setBrightness);
          FastLED.show();
        }
      }
      break;
    case /* constant-expression */ CMD_Programming_mode:
      /* code */
      {
      }
      break;
    default:
      break;
    }
  }
}

/*Standby mode*/
void ApplicationFunctionSet::ApplicationFunctionSet_Standby(void)
{
  if (Application_SmartRobotCarxxx0.Functional_Mode == Standby_mode)
  {
    ApplicationFunctionSet_SmartRobotCarMotionControl(stop_it, 0);
  }
}

/* 
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
 * Begin:CMD
 * Graphical programming and command control module
 $ Elegoo & SmartRobot & 2020-06
*/

void ApplicationFunctionSet::CMD_inspect_xxx0(void)
{
  if (Application_SmartRobotCarxxx0.Functional_Mode == CMD_inspect)
  {
    Serial.println("CMD_inspect");
    delay(100);
  }
}
static void CMD_CarControl(uint8_t is_CarDirection, uint8_t is_CarSpeed)
{
  switch (is_CarDirection)
  {
  case 1: 
    ApplicationFunctionSet_SmartRobotCarMotionControl(Left, is_CarSpeed);
    break;
  case 2: 
    ApplicationFunctionSet_SmartRobotCarMotionControl(Right, is_CarSpeed);
    break;
  case 3: /*movement direction mode forward*/
    ApplicationFunctionSet_SmartRobotCarMotionControl(Forward, is_CarSpeed);
    break;
  case 4: /*movement direction mode backward*/
    ApplicationFunctionSet_SmartRobotCarMotionControl(Backward, is_CarSpeed);
    break;
  default:
    break;
  }
}
/*
  N2：command
  CMD mode：Receive the control commands from the APP,perform movement direction and speed control of the car
  Time limited
*/
void ApplicationFunctionSet::CMD_CarControlTimeLimit_xxx0(uint8_t is_CarDirection, uint8_t is_CarSpeed, uint32_t is_Timer)
{
  static boolean CarControl = false;
  static boolean CarControl_TE = false; //Time stamp
  static boolean CarControl_return = false;
  if (Application_SmartRobotCarxxx0.Functional_Mode == CMD_CarControl_TimeLimit) //enter time-limited control mode
  {
    CarControl = true;
    if (is_Timer != 0) //#1 if the pre-set time is not ... (zero)
    {
      if ((millis() - Application_SmartRobotCarxxx0.CMD_CarControl_Millis) > (is_Timer)) //check the timestamp
      {
        CarControl_TE = true;
        ApplicationFunctionSet_SmartRobotCarMotionControl(stop_it, 0);

        Application_SmartRobotCarxxx0.Functional_Mode = CMD_Programming_mode; /*set mode to programming mode<Waiting for the next set of control commands>*/
        if (CarControl_return == false)
        {

#if _is_print
          Serial.print('{' + CommandSerialNumber + "_ok}");
#endif
          CarControl_return = true;
        }
      }
      else
      {
        CarControl_TE = false; //There still has time left
        CarControl_return = false;
      }
    }
    if (CarControl_TE == false)
    {
      CMD_CarControl(is_CarDirection, is_CarSpeed);
    }
  }
  else
  {
    if (CarControl == true)
    {
      CarControl_return = false;
      CarControl = false;
      Application_SmartRobotCarxxx0.CMD_CarControl_Millis = 0;
    }
  }
}

void ApplicationFunctionSet::CMD_CarControlTimeLimit_xxx0(void)
{
  static boolean CarControl = false;
  static boolean CarControl_TE = false; //Time stamp
  static boolean CarControl_return = false;
  if (Application_SmartRobotCarxxx0.Functional_Mode == CMD_CarControl_TimeLimit) //enter time-limited control mode
  {
    CarControl = true;
    if (CMD_is_CarTimer != 0) //#1 if the pre-set time is not ... (zero)
    {
      if ((millis() - Application_SmartRobotCarxxx0.CMD_CarControl_Millis) > (CMD_is_CarTimer)) //check the timestamp
      {
        CarControl_TE = true;
        ApplicationFunctionSet_SmartRobotCarMotionControl(stop_it, 0);

        Application_SmartRobotCarxxx0.Functional_Mode = CMD_Programming_mode; /*set mode to programming mode<Waiting for the next set of control commands>*/
        if (CarControl_return == false)
        {

#if _is_print
          Serial.print('{' + CommandSerialNumber + "_ok}");
#endif
          CarControl_return = true;
        }
      }
      else
      {
        CarControl_TE = false; //There still has time left
        CarControl_return = false;
      }
    }
    if (CarControl_TE == false)
    {
      CMD_CarControl(CMD_is_CarDirection, CMD_is_CarSpeed);
    }
  }
  else
  {
    if (CarControl == true)
    {
      CarControl_return = false;
      CarControl = false;
      Application_SmartRobotCarxxx0.CMD_CarControl_Millis = 0;
    }
  }
}
/*
  N5:command
  CMD mode：<servo motor control>
*/
void ApplicationFunctionSet::CMD_ServoControl_xxx0(void)
{
  if (Application_SmartRobotCarxxx0.Functional_Mode == CMD_ServoControl)
  {
    AppServo.DeviceDriverSet_Servo_degrees(CMD_is_Servo, CMD_is_Servo_angle);
    Application_SmartRobotCarxxx0.Functional_Mode = CMD_Programming_mode; /*set mode to programming mode<Waiting for the next set of control commands>*/
  }
}
/*
  N100:command
  CMD mode：Clear all functions
*/
void ApplicationFunctionSet::CMD_ClearAllFunctions_xxx0(void)
{
  if (Application_SmartRobotCarxxx0.Functional_Mode == CMD_ClearAllFunctions_Standby_mode) //Command:N100 Clear all functions to enter standby mode
  {
    ApplicationFunctionSet_SmartRobotCarMotionControl(stop_it, 0);
    FastLED.clear(true);
    AppRBG_LED.DeviceDriverSet_RBGLED_xxx(0 /*Duration*/, NUM_LEDS /*Traversal_Number*/, CRGB::Black);
    Application_SmartRobotCarxxx0.Motion_Control = stop_it;
    Application_SmartRobotCarxxx0.Functional_Mode = Standby_mode;
  }
}

/*
  N21:command
  CMD mode：The ultrasonic module receives and feeds back status and raw echo duration in microseconds.
  Input：
*/
void ApplicationFunctionSet::CMD_UltrasoundModuleStatus_xxx0(uint8_t is_get, unsigned long timeoutUs)
{
  AppULTRASONIC.DeviceDriverSet_ULTRASONIC_Get(&UltrasoundPulse_us /*out*/, timeoutUs); //Raw echo duration in microseconds
  UltrasoundDetectionStatus = function_xxx(UltrasoundPulse_us, 0, ObstacleDetection);
  if (1 == is_get) //ultrasonic sensor  is_get Start     true：has obstacle / false: no obstable
  {
    if (true == UltrasoundDetectionStatus)
    {
#if _is_print
      Serial.print('{' + CommandSerialNumber + "_true}");
#endif
    }
    else
    {
#if _is_print
      Serial.print('{' + CommandSerialNumber + "_false}");
#endif
    }
  }
  else if (2 == is_get) //ultrasonic sensor is_get data
  {
    char toString[11];
    sprintf(toString, "%lu", UltrasoundPulse_us);
#if _is_print
    Serial.print('{' + CommandSerialNumber + '_' + toString + '}');
#endif
  }
}
/**
 * Read battery voltage on request and send a tagged decimal reply in volts.
 * No parameters or return value. Uses the existing A3 conversion and the
 * current CommandSerialNumber string; reports three fractional digits and
 * leaves the current functional mode unchanged. Calibration is unverified.
 */
void ApplicationFunctionSet::CMD_VoltageMeasurement_xxx0(void)
{
  const float Voltage = AppVoltage.DeviceDriverSet_Voltage_getAnalogue();
  char toString[16];
  dtostrf(Voltage, 1, 3, toString);
#if _is_print
  Serial.print('{' + CommandSerialNumber + '_' + toString + '}');
#endif
}

/**
 * Read raw X/Y/Z gyro counts and send a tagged comma-separated reply.
 * No parameters or return value. Uses CommandSerialNumber as the reply tag and
 * signed 16-bit sensor counts in X,Y,Z order. Performs no offset subtraction,
 * unit conversion, calibration, yaw integration, or functional-mode change.
 */
void ApplicationFunctionSet::CMD_GyroMeasurement_xxx0(void)
{
  int16_t x, y, z;
  AppMPU6050getdata.MPU6050_getRawRotation(&x, &y, &z);
  char toString[24];
  sprintf(toString, "%d,%d,%d", x, y, z);
#if _is_print
  Serial.print('{' + CommandSerialNumber + '_' + toString + '}');
#endif
}

/**
 * Read raw X/Y/Z accelerometer counts and send a tagged comma-separated reply.
 * No parameters or return value. Uses CommandSerialNumber as the reply tag and
 * signed 16-bit sensor counts in X,Y,Z order, including gravity's contribution.
 * Performs no unit conversion, calibration, or functional-mode change.
 */
void ApplicationFunctionSet::CMD_AccelerationMeasurement_xxx0(void)
{
  int16_t x, y, z;
  AppMPU6050getdata.MPU6050_getRawAcceleration(&x, &y, &z);
  char toString[24];
  sprintf(toString, "%d,%d,%d", x, y, z);
#if _is_print
  Serial.print('{' + CommandSerialNumber + '_' + toString + '}');
#endif
}

/**
 * Apply a host-requested pan increment and acknowledge after driver execution.
 * stepDegrees is a signed 16-bit degree step supplied by the host. There is no
 * return value. Commands only pan, then sets programming mode and sends a reply
 * tagged with CommandSerialNumber. The acknowledgment does not measure position.
 */
void ApplicationFunctionSet::CMD_PanIncrement_xxx0(int16_t stepDegrees)
{
  AppServo.DeviceDriverSet_Servo_increment(stepDegrees);
  Application_SmartRobotCarxxx0.Functional_Mode = CMD_Programming_mode;
#if _is_print
  Serial.print('{' + CommandSerialNumber + "_ok}");
#endif
}

/*
  N22:command
  CMD mode：Read and return the selected raw floor-sensor value on request.
  Input：
*/
void ApplicationFunctionSet::CMD_TraceModuleStatus_xxx0(uint8_t is_get)
{
  char toString[10];
  if (0 == is_get) /*Get left IR sensor status*/
  {
    sprintf(toString, "%d", AppITR20001.DeviceDriverSet_ITR20001_getAnaloguexxx_L());
#if _is_print
    Serial.print('{' + CommandSerialNumber + '_' + toString + '}');
#endif
  }
  else if (1 == is_get) /*Get middle IR sensor status*/
  {
    sprintf(toString, "%d", AppITR20001.DeviceDriverSet_ITR20001_getAnaloguexxx_M());
#if _is_print
    Serial.print('{' + CommandSerialNumber + '_' + toString + '}');
#endif
  }
  else if (2 == is_get) /*Get right IR sensor status*/
  {
    sprintf(toString, "%d", AppITR20001.DeviceDriverSet_ITR20001_getAnaloguexxx_R());
#if _is_print
    Serial.print('{' + CommandSerialNumber + '_' + toString + '}');
#endif
  }
}

/* 
 * End:CMD
 * Graphical programming and command control module
 $ Elegoo & SmartRobot & 2020-06
 --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


/*Key command*/
void ApplicationFunctionSet::ApplicationFunctionSet_KeyCommand(void)
{
  uint8_t get_keyValue;
  static uint8_t temp_keyValue = keyValue_Max;
  AppKey.DeviceDriverSet_key_Get(&get_keyValue);

  if (temp_keyValue != get_keyValue)
  {
    temp_keyValue = get_keyValue;//Serial.println(get_keyValue);
    switch (get_keyValue)
    {
    case /* constant-expression */ 4:
      /* code */
      Application_SmartRobotCarxxx0.Functional_Mode = Standby_mode;
      break;
    default:

      break;
    }
  }
}
/*Data analysis on serial port*/
void ApplicationFunctionSet::ApplicationFunctionSet_SerialPortDataAnalysis(void)
{
  static String SerialPortData = "";
  uint8_t c = "";
  if (Serial.available() > 0)
  {
    while (c != '}' && Serial.available() > 0)
    {
      // while (Serial.available() == 0)//Forcibly wait for a frame of data to be received
      //   ;
      c = Serial.read();
      SerialPortData += (char)c;
    }
  }
  if (c == '}') //Data frame tail check
  {
#if _Test_print
    Serial.println(SerialPortData);
#endif
    // if (true == SerialPortData.equals("{f}") || true == SerialPortData.equals("{b}") || true == SerialPortData.equals("{l}") || true == SerialPortData.equals("{r}"))
    // {
    //   Serial.print(SerialPortData);
    //   SerialPortData = "";
    //   return;
    // }
    // if (true == SerialPortData.equals("{Factory}") || true == SerialPortData.equals("{WA_NO}") || true == SerialPortData.equals("{WA_OK}")) 
    // {
    //   SerialPortData = "";
    //   return;
    // }
    StaticJsonDocument<200> doc;                                       //Declare a JsonDocument object
    DeserializationError error = deserializeJson(doc, SerialPortData); //Deserialize JSON data from the serial data buffer
    SerialPortData = "";
    if (error)
    {
      Serial.println("error:deserializeJson");
    }
    else if (!error) //Check if the deserialization is successful
    {
      int control_mode_N = doc["N"];
      char *temp = doc["H"];
      CommandSerialNumber = temp; //Get the serial number of the new command

      /*Please view the following code blocks in conjunction with the Communication protocol for Smart Robot Car.pdf*/
      switch (control_mode_N)
      {
      case 2:                                                                     /*<Command：N 2> */
        Application_SmartRobotCarxxx0.Functional_Mode = CMD_CarControl_TimeLimit; /*Car movement direction and speed control：Time limited mode*/
        CMD_is_CarDirection = doc["D1"];
        CMD_is_CarSpeed = doc["D2"];
        CMD_is_CarTimer = doc["T"];
        Application_SmartRobotCarxxx0.CMD_CarControl_Millis = millis();
#if _is_print
        //Serial.print('{' + CommandSerialNumber + "_ok}");
#endif
        break;

      case 5:                                                             /*<Command：N 5> */
        Application_SmartRobotCarxxx0.Functional_Mode = CMD_ServoControl; /*servo motor control*/
        CMD_is_Servo = doc["D1"];
        CMD_is_Servo_angle = doc["D2"];
#if _is_print
        Serial.print('{' + CommandSerialNumber + "_ok}");
#endif
        break;
      case 21: /*<Command：N 21>：ultrasonic sensor: raw echo duration; T is timeout in microseconds */
        CMD_UltrasoundModuleStatus_xxx0(doc["D1"], doc["T"]);
#if _is_print
        //Serial.print('{' + CommandSerialNumber + "_ok}");
#endif
        break;

      case 22: /*<Command：N 22>：read selected raw floor sensor on request */
        CMD_TraceModuleStatus_xxx0(doc["D1"]);
#if _is_print
        //Serial.print('{' + CommandSerialNumber + "_ok}");
#endif
        break;

      case 24: /*<Command：N 24>：read estimated battery voltage on request */
        CMD_VoltageMeasurement_xxx0();
        break;

      case 25: /*<Command：N 25>：read raw X/Y/Z gyro counts on request */
        CMD_GyroMeasurement_xxx0();
        break;

      case 26: /*<Command：N 26>：read raw X/Y/Z accelerometer counts on request */
        CMD_AccelerationMeasurement_xxx0();
        break;

      case 27: /*<Command：N 27>：signed pan-only degree increment */
        CMD_PanIncrement_xxx0(doc["D1"]);
        break;

      case 100:                                                                             /*<Command：N 100> */
        Application_SmartRobotCarxxx0.Functional_Mode = CMD_ClearAllFunctions_Standby_mode; /*Clear all function:Enter standby mode*/
#if _is_print
        Serial.print("{ok}");
        //Serial.print('{' + CommandSerialNumber + "_ok}");
#endif
        break;


      default:
        break;
      }
    }
  }
}
