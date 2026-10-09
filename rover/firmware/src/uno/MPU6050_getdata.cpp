#include <Wire.h>

#include "MPU6050.h"
#include "MPU6050_getdata.h"

bool MPU6050_getdata::readBytes(uint8_t reg, uint8_t *data, uint8_t count)
{
  Wire.clearWireTimeoutFlag();
  Wire.beginTransmission(MPU6050_DEFAULT_ADDRESS);
  Wire.write(reg);
  if (Wire.endTransmission() != 0 || Wire.getWireTimeoutFlag()) return false;
  if (Wire.requestFrom(uint8_t(MPU6050_DEFAULT_ADDRESS), count) != count ||
      Wire.getWireTimeoutFlag()) return false;
  for (uint8_t i = 0; i < count; ++i)
  {
    const int value = Wire.read();
    if (value < 0) return false;
    data[i] = uint8_t(value);
  }
  return true;
}

bool MPU6050_getdata::configure(uint8_t reg, uint8_t mask, uint8_t value)
{
  uint8_t previous;
  if (!readBytes(reg, &previous, 1)) return false;
  Wire.clearWireTimeoutFlag();
  Wire.beginTransmission(MPU6050_DEFAULT_ADDRESS);
  Wire.write(reg);
  Wire.write(uint8_t((previous & ~mask) | value));
  if (Wire.endTransmission() != 0 || Wire.getWireTimeoutFlag()) return false;
  uint8_t actual;
  return readBytes(reg, &actual, 1) && (actual & mask) == value;
}

bool MPU6050_getdata::MPU6050_dveInit()
{
  initialized = false;
  Wire.begin();
  // Core 1.8.8 supports bounded TWI waits and bus reset. This is a per-Wire-
  // operation limit, not a measured end-to-end command or physical stop bound.
  Wire.setWireTimeout(10000, true);
  for (uint8_t attempt = 0; attempt < 10; ++attempt)
  {
    uint8_t identity;
    if (readBytes(MPU6050_RA_WHO_AM_I, &identity, 1) && (identity & 0x7e) == 0x68 &&
        configure(MPU6050_RA_PWR_MGMT_1, 0x47, MPU6050_CLOCK_PLL_XGYRO) &&
        configure(MPU6050_RA_GYRO_CONFIG, 0x18, MPU6050_GYRO_FS_250) &&
        configure(MPU6050_RA_ACCEL_CONFIG, 0x18, MPU6050_ACCEL_FS_2))
    {
      initialized = true;
      return true;
    }
    delay(10);
  }
  return false;
}

bool MPU6050_getdata::readVector(uint8_t reg, int16_t *x, int16_t *y, int16_t *z)
{
  if (!initialized) return false;
  uint8_t data[6];
  if (!readBytes(reg, data, sizeof(data)))
  {
    initialized = false;
    return false;
  }
  *x = int16_t((uint16_t(data[0]) << 8) | data[1]);
  *y = int16_t((uint16_t(data[2]) << 8) | data[3]);
  *z = int16_t((uint16_t(data[4]) << 8) | data[5]);
  return true;
}

bool MPU6050_getdata::MPU6050_getRawRotation(int16_t *x, int16_t *y, int16_t *z)
{
  return readVector(MPU6050_RA_GYRO_XOUT_H, x, y, z);
}

bool MPU6050_getdata::MPU6050_getRawAcceleration(int16_t *x, int16_t *y, int16_t *z)
{
  return readVector(MPU6050_RA_ACCEL_XOUT_H, x, y, z);
}
