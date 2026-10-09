# Preserved yaw integration function

Source: rover/firmware/src/uno/MPU6050_getdata.cpp. Tagged for removal during review; the active function has not been removed.

```cpp
bool MPU6050_getdata::MPU6050_dveGetEulerAngles(float *Yaw)
{
  unsigned long now = millis();           //Record the current time(ms)
  dt = (now - lastTime) / 1000.0;         //Caculate the derivative time(s)
  lastTime = now;                         //Record the last sampling time(ms)
  gz = accelgyro.getRotationZ();          //Read the raw values of the six axes
  float gyroz = -(gz - gzo) / 131.0 * dt; //z-axis angular velocity
  if (fabs(gyroz) < 0.05)                 //Clear instant zero drift signal
  {
    gyroz = 0.00;
  }
  agz += gyroz; //z-axis angular velocity integral
  *Yaw = agz;
  return false;
}
```
