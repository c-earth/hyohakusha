/*
 * @Author: ELEGOO
 * @Date: 2019-10-22 11:59:09
 * @LastEditTime: 2020-12-29 16:02:26
 * @LastEditors: Changhua
 * @Description: Smart Robot Car V4.0
 * @FilePath: 
 */
#ifndef _DeviceDriverSet_xxx0_H_
#define _DeviceDriverSet_xxx0_H_

#define _Test_DeviceDriverSet 0

/*RBG LED*/
#include "FastLED.h"
class DeviceDriverSet_RBGLED
{
public:
  void DeviceDriverSet_RBGLED_Init(uint8_t set_Brightness);
  void DeviceDriverSet_RBGLED_xxx(uint16_t Duration, uint8_t Traversal_Number, CRGB colour);
#if _Test_DeviceDriverSet
  void DeviceDriverSet_RBGLED_Test(void);
#endif
  void DeviceDriverSet_RBGLED_Color(uint8_t LED_s, uint8_t r, uint8_t g, uint8_t b);

public:
private:
#define PIN_RBGLED 4
#define NUM_LEDS 1
public:
  CRGB leds[NUM_LEDS];
};

/*Key Detection*/
class DeviceDriverSet_Key
{
public:
  void DeviceDriverSet_Key_Init(void);
#if _Test_DeviceDriverSet
  void DeviceDriverSet_Key_Test(void);
#endif
  void DeviceDriverSet_key_Get(uint8_t *get_keyValue);

public:
#define PIN_Key 2
#define keyValue_Max 4
public:
  static uint8_t keyValue;
};

/*ITR20001 Detection*/
class DeviceDriverSet_ITR20001
{
public:
  bool DeviceDriverSet_ITR20001_Init(void);
  int DeviceDriverSet_ITR20001_getAnaloguexxx_L(void);
  int DeviceDriverSet_ITR20001_getAnaloguexxx_M(void);
  int DeviceDriverSet_ITR20001_getAnaloguexxx_R(void);
#if _Test_DeviceDriverSet
  void DeviceDriverSet_ITR20001_Test(void);
#endif

private:
//03
// #define PIN_ITR20001xxxL A0
// #define PIN_ITR20001xxxM A1
// #define PIN_ITR20001xxxR A2
//04
#define PIN_ITR20001xxxL A2
#define PIN_ITR20001xxxM A1
#define PIN_ITR20001xxxR A0
};

/*Voltage Detection*/
class DeviceDriverSet_Voltage
{
public:
  void DeviceDriverSet_Voltage_Init(void);
  float DeviceDriverSet_Voltage_getAnalogue(void);
#if _Test_DeviceDriverSet
  void DeviceDriverSet_Voltage_Test(void);
#endif
private:
#define PIN_Voltage A3
};

/*Motor*/
class DeviceDriverSet_Motor
{
public:
  void DeviceDriverSet_Motor_Init(void);
#if _Test_DeviceDriverSet
  void DeviceDriverSet_Motor_Test(void);
#endif
  void DeviceDriverSet_Motor_control(boolean direction_A, uint8_t speed_A, //Group A motor parameters
                                     boolean direction_B, uint8_t speed_B, //Group B motor parameters
                                     boolean controlED                     //AB enable setting (true)
  );                                                                       //motor control
private:
  // #define PIN_Motor_PWMA 5
  // #define PIN_Motor_PWMB 6
  // #define PIN_Motor_STBY 8
  // #define PIN_Motor_BIN_1 7
  // #define PIN_Motor_AIN_1 9
//TB6612
#define PIN_Motor_PWMA 5
#define PIN_Motor_PWMB 6
#define PIN_Motor_BIN_1 8
#define PIN_Motor_AIN_1 7
#define PIN_Motor_STBY 3
public:
#define speed_Max 255
#define direction_just true
#define direction_back false
#define direction_void 3

#define Duration_enable true
#define Duration_disable false
#define control_enable true
#define control_disable false
};
/*ULTRASONIC*/

//#include <NewPing.h>
class DeviceDriverSet_ULTRASONIC
{
public:
  void DeviceDriverSet_ULTRASONIC_Init(void);
#if _Test_DeviceDriverSet
  void DeviceDriverSet_ULTRASONIC_Test(void);
#endif
  void DeviceDriverSet_ULTRASONIC_Get(unsigned long *ULTRASONIC_Get /*out*/, unsigned long timeoutUs);

private:
#define TRIG_PIN 13      // Arduino pin tied to trigger pin on the ultrasonic sensor.
#define ECHO_PIN 12      // Arduino pin tied to echo pin on the ultrasonic sensor.
#define MAX_DISTANCE 200 // Maximum distance we want to ping for (in centimeters). Maximum sensor distance is rated at 400-500cm.
};
/*Servo*/
#include <Servo.h>
class DeviceDriverSet_Servo
{
public:
  void DeviceDriverSet_Servo_Init(unsigned int Position_angle);
#if _Test_DeviceDriverSet
  void DeviceDriverSet_Servo_Test(void);
#endif
  void DeviceDriverSet_Servo_control(unsigned int Position_angle);
  void DeviceDriverSet_Servo_increment(int16_t stepDegrees);
  void DeviceDriverSet_Servo_degrees(uint8_t Servo, unsigned int Position_angle);

private:
#define PIN_Servo_z 10
#define PIN_Servo_y 11
  unsigned int panAngleDegrees = 90;
};
#endif
