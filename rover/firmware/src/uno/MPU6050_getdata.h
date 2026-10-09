#ifndef _MPU6050_getdata_H_
#define _MPU6050_getdata_H_

#include <Arduino.h>

// Checked raw MPU6050 access; readiness is latched false after a failed read.
// Recovery requires initialization at board restart, never a silent bias retry.
class MPU6050_getdata
{
public:
  // Return true only after identity, configuration writes and readback succeed.
  bool MPU6050_dveInit();
  bool ready() const { return initialized; }
  // Non-null outputs receive signed raw XYZ counts only on success (true).
  bool MPU6050_getRawRotation(int16_t *x, int16_t *y, int16_t *z);
  bool MPU6050_getRawAcceleration(int16_t *x, int16_t *y, int16_t *z);

private:
  bool readBytes(uint8_t reg, uint8_t *data, uint8_t count);
  bool configure(uint8_t reg, uint8_t mask, uint8_t value);
  bool readVector(uint8_t reg, int16_t *x, int16_t *y, int16_t *z);
  bool initialized = false;
};

#endif
