// Host-directed UNO command application; no onboard navigation or yaw control.
#ifndef _ApplicationFunctionSet_xxx0_H_
#define _ApplicationFunctionSet_xxx0_H_

#include <Arduino.h>
#include "DriveTimer.h"

class ApplicationFunctionSet
{
public:
  void ApplicationFunctionSet_Init();
  void ApplicationFunctionSet_SerialPortDataAnalysis();
  void CMD_CarControlTimeLimit_xxx0();

private:
  void stopDrive();
  void reply(const String &tag, const char *payload);
  void fail(const __FlashStringHelper *reason);
  void CMD_UltrasoundModuleStatus_xxx0(uint8_t is_get, unsigned long timeoutUs);
  void CMD_TraceModuleStatus_xxx0(uint8_t is_get);
  void CMD_VoltageMeasurement_xxx0();
  void CMD_ImuMeasurement(bool gyro);

  String commandTag;
  String driveTag;
  String serialData;
  DriveTimer drive;
};

extern ApplicationFunctionSet Application_FunctionSet;
#endif
