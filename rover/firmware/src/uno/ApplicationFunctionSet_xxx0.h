/*
 * @Author: ELEGOO
 * @Date: 2019-10-22 11:59:09
 * @LastEditTime: 2020-12-29 16:04:05
 * @LastEditors: Changhua
 * @Description: Smart Robot Car V4.0
 * @FilePath: 
 */
#ifndef _ApplicationFunctionSet_xxx0_H_
#define _ApplicationFunctionSet_xxx0_H_

#include <Arduino.h>

class ApplicationFunctionSet
{
public:
  void ApplicationFunctionSet_Init(void);
  void ApplicationFunctionSet_Bootup(void);
  void ApplicationFunctionSet_RGB(void);
  void ApplicationFunctionSet_Expression(void);
  void ApplicationFunctionSet_Standby(void);            //Standby Mode
  void ApplicationFunctionSet_KeyCommand(void);         //Mode Switch Button
  void ApplicationFunctionSet_SensorDataUpdate(void);   //Sensor Data Update
  void ApplicationFunctionSet_SerialPortDataAnalysis(void);

public: /*CMD*/
  void CMD_UltrasoundModuleStatus_xxx0(uint8_t is_get, unsigned long timeoutUs);
  void CMD_TraceModuleStatus_xxx0(uint8_t is_get);
  void CMD_VoltageMeasurement_xxx0(void);
  void CMD_GyroMeasurement_xxx0(void);
  void CMD_AccelerationMeasurement_xxx0(void);
  void CMD_PanIncrement_xxx0(int16_t stepDegrees);

  void CMD_inspect_xxx0(void);
  void CMD_CarControlTimeLimit_xxx0(void);
  void CMD_CarControlTimeLimit_xxx0(uint8_t is_CarDirection, uint8_t is_CarSpeed, uint32_t is_Timer);
  void CMD_ServoControl_xxx0(void);
  void CMD_VoiceControl_xxx0(uint16_t is_VoiceName, uint32_t is_VoiceTimer);
  void CMD_LEDCustomExpressionControl_xxx0(void);
  void CMD_ClearAllFunctions_xxx0(void);
  void CMD_LEDNumberDisplayControl_xxx0(uint8_t is_LEDNumber);
  void CMD_TrajectoryControl_xxx0(void);

private:
  /*Sensor Raw Value*/
  volatile float VoltageData_V;        //Battery Voltage Value
  unsigned long UltrasoundPulse_us; //Raw echo duration in microseconds; zero means timeout.
  /*Sensor Status*/
  boolean VoltageDetectionStatus = false;
  boolean UltrasoundDetectionStatus = false;

public:

  /*Sensor Threshold Setting*/
  const float VoltageDetection = 7.00;
  const uint8_t ObstacleDetection = 20;

  String CommandSerialNumber;

public:

public:
  uint8_t CMD_is_Servo;
  uint8_t CMD_is_Servo_angle;

public:

public:
  uint8_t CMD_is_CarDirection; //car
  uint8_t CMD_is_CarSpeed;
  uint32_t CMD_is_CarTimer;

public:

public:

private:
};
extern ApplicationFunctionSet Application_FunctionSet;
#endif
