// Command IDs, direct PWM, raw sensor units and 9600-baud UART remain unchanged.
#include <stdio.h>

#include "ApplicationFunctionSet_xxx0.h"
#include "DeviceDriverSet_xxx0.h"
#include "ArduinoJson-v6.11.1.h"
#include "MPU6050_getdata.h"

ApplicationFunctionSet Application_FunctionSet;

static MPU6050_getdata AppMPU6050getdata;
static DeviceDriverSet_RBGLED AppRBG_LED;
static DeviceDriverSet_ITR20001 AppITR20001;
static DeviceDriverSet_Voltage AppVoltage;
static DeviceDriverSet_Motor AppMotor;
static DeviceDriverSet_ULTRASONIC AppULTRASONIC;
static DeviceDriverSet_Servo AppServo;

void ApplicationFunctionSet::ApplicationFunctionSet_Init()
{
  Serial.begin(9600);
  AppVoltage.DeviceDriverSet_Voltage_Init();
  AppMotor.DeviceDriverSet_Motor_Init();
  stopDrive();
  AppServo.DeviceDriverSet_Servo_Init(90);
  AppRBG_LED.DeviceDriverSet_RBGLED_Init(20);
  AppULTRASONIC.DeviceDriverSet_ULTRASONIC_Init();
  AppITR20001.DeviceDriverSet_ITR20001_Init();
  // Initialization owns readiness. N2/N3/N4 report failure if it did not pass.
  AppMPU6050getdata.MPU6050_dveInit();
}

void ApplicationFunctionSet::stopDrive()
{
  AppMotor.DeviceDriverSet_Motor_control(direction_void, 0, direction_void, 0, control_enable);
  drive = DriveTimer();
}

void ApplicationFunctionSet::reply(const String &tag, const char *payload)
{
  Serial.print('{');
  Serial.print(tag);
  Serial.print('_');
  Serial.print(payload);
  Serial.print('}');
}

// Every explicit fault stops motor output before potentially blocking UART I/O.
void ApplicationFunctionSet::fail(const __FlashStringHelper *reason)
{
  stopDrive();
  Serial.print('{');
  if (commandTag.length())
  {
    Serial.print(commandTag);
    Serial.print('_');
  }
  Serial.print(F("error_"));
  Serial.print(reason);
  Serial.print('}');
}

void ApplicationFunctionSet::CMD_CarControlTimeLimit_xxx0()
{
  if (drive.expired(millis()))
  {
    stopDrive();
    // Sensor requests can change commandTag, but never this N4-owned tag.
    reply(driveTag, "ok");
  }
}

void ApplicationFunctionSet::CMD_UltrasoundModuleStatus_xxx0(uint8_t is_get, unsigned long timeoutUs)
{
  unsigned long pulseUs = 0;
  AppULTRASONIC.DeviceDriverSet_ULTRASONIC_Get(&pulseUs, timeoutUs);
  if (is_get == 1)
  {
    // Preserve the legacy boolean threshold. Hosts use raw D1=2; not calibrated.
    reply(commandTag, pulseUs <= 20 ? "true" : "false");
  }
  else if (is_get == 2)
  {
    char value[11];
    sprintf(value, "%lu", pulseUs);
    reply(commandTag, value);
  }
}

void ApplicationFunctionSet::CMD_VoltageMeasurement_xxx0()
{
  char value[16];
  dtostrf(AppVoltage.DeviceDriverSet_Voltage_getAnalogue(), 1, 3, value);
  CMD_CarControlTimeLimit_xxx0();
  reply(commandTag, value);
}

void ApplicationFunctionSet::CMD_ImuMeasurement(bool gyro)
{
  if (!AppMPU6050getdata.ready())
  {
    fail(F("imu_not_ready"));
    return;
  }
  int16_t x, y, z;
  bool valid = gyro ? AppMPU6050getdata.MPU6050_getRawRotation(&x, &y, &z)
                    : AppMPU6050getdata.MPU6050_getRawAcceleration(&x, &y, &z);
  if (!valid)
  {
    fail(F("imu_read"));
    return;
  }
  CMD_CarControlTimeLimit_xxx0();
  char value[24];
  sprintf(value, "%d,%d,%d", x, y, z);
  reply(commandTag, value);
}

void ApplicationFunctionSet::CMD_TraceModuleStatus_xxx0(uint8_t is_get)
{
  int reading;
  switch (is_get)
  {
  case 0: reading = AppITR20001.DeviceDriverSet_ITR20001_getAnaloguexxx_L(); break;
  case 1: reading = AppITR20001.DeviceDriverSet_ITR20001_getAnaloguexxx_M(); break;
  case 2: reading = AppITR20001.DeviceDriverSet_ITR20001_getAnaloguexxx_R(); break;
  default: return;
  }
  CMD_CarControlTimeLimit_xxx0();
  char value[10];
  sprintf(value, "%d", reading);
  reply(commandTag, value);
}

void ApplicationFunctionSet::ApplicationFunctionSet_SerialPortDataAnalysis()
{
  // Bound partial frames and service expiry even while incoming bytes continue.
  while (Serial.available() > 0)
  {
    CMD_CarControlTimeLimit_xxx0();
    const char c = char(Serial.read());
    if (c == '{') serialData = "";
    if (serialData.length() == 0 && c != '{') continue;
    if (serialData.length() >= 160)
    {
      serialData = "";
      commandTag = "";
      fail(F("frame_too_long"));
      return;
    }
    serialData += c;
    if (c != '}') continue;

    StaticJsonDocument<200> doc;
    const DeserializationError error = deserializeJson(doc, serialData);
    serialData = "";
    commandTag = "";
    if (error)
    {
      fail(F("bad_json"));
      return;
    }
    const char *tag = doc["H"];
    if (tag) commandTag = tag;
    const int number = doc["N"];

    // N100 stops synchronously, including the camera's untagged disconnect stop.
    if (number == 100)
    {
      stopDrive();
      Serial.print(F("{ok}"));
      return;
    }
    CMD_CarControlTimeLimit_xxx0();
    if (drive.active() && (number == 5 || number == 6 || number == 7))
    {
      fail(F("drive_busy"));
      return;
    }

    switch (number)
    {
    case 1: CMD_VoltageMeasurement_xxx0(); break;
    case 2: CMD_ImuMeasurement(true); break;
    case 3: CMD_ImuMeasurement(false); break;
    case 4:
    {
      if (!AppMPU6050getdata.ready())
      {
        fail(F("imu_not_ready"));
        break;
      }
      const uint8_t direction = doc["D1"];
      const uint8_t speed = doc["D2"];
      if (direction < 1 || direction > 4)
      {
        fail(F("drive_direction"));
        break;
      }
      driveTag = commandTag;
      drive = DriveTimer(millis(), doc["T"].as<uint32_t>());
      // Same A/B polarity and PWM as the installed direct-drive implementation.
      const bool directionA = direction == 1 || direction == 3;
      const bool directionB = direction == 2 || direction == 3;
      AppMotor.DeviceDriverSet_Motor_control(directionA, speed, directionB, speed, control_enable);
      break;
    }
    case 5:
      AppServo.DeviceDriverSet_Servo_degrees(doc["D1"], doc["D2"]);
      reply(commandTag, "ok");
      break;
    case 6:
      AppServo.DeviceDriverSet_Servo_increment(doc["D1"]);
      reply(commandTag, "ok");
      break;
    case 7: CMD_UltrasoundModuleStatus_xxx0(doc["D1"], doc["T"]); break;
    case 8: CMD_TraceModuleStatus_xxx0(doc["D1"]); break;
    default: break;
    }
    return;
  }
}
