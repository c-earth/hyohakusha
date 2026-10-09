#ifndef ROVER_DRIVE_TIMER_H
#define ROVER_DRIVE_TIMER_H

#include <stdint.h>

// Independent of sensor/servo modes. Times are unsigned millis() values;
// duration 0 retains the existing no-expiry contract. Default state is stopped.
class DriveTimer
{
public:
  constexpr DriveTimer() : startedMs(0), durationMs(0), running(false) {}
  constexpr DriveTimer(uint32_t start, uint32_t duration)
      : startedMs(start), durationMs(duration), running(true) {}
  constexpr bool active() const { return running; }
  constexpr bool expired(uint32_t now) const
  {
    return running && durationMs != 0 && uint32_t(now - startedMs) >= durationMs;
  }

private:
  uint32_t startedMs;
  uint32_t durationMs;
  bool running;
};

#endif
