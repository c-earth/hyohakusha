// Compile with the local AVR compiler. These assertions evaluate the actual
// production timer; no board, simulator or native C++ runtime is required.
#include "../src/uno/DriveTimer.h"

static_assert(!DriveTimer().active(), "Default timer must be stopped");
static_assert(!DriveTimer().expired(100), "Stopped timer must not complete");
static_assert(DriveTimer(100, 200).active(), "N4 starts the timer");
static_assert(!DriveTimer(100, 200).expired(299), "Do not expire early");
static_assert(DriveTimer(100, 200).expired(300), "Expire at the exact deadline");
static_assert(DriveTimer(100, 200).expired(301), "Late service must expire");
static_assert(!DriveTimer(100, 0).expired(0xffffffffUL), "T=0 keeps no-expiry contract");
static_assert(!DriveTimer(0xfffffff0UL, 32).expired(15), "Wraparound must not expire early");
static_assert(DriveTimer(0xfffffff0UL, 32).expired(16), "Expire across millis wraparound");
static_assert(!DriveTimer(250, 200).expired(300), "Renewed N4 has a fresh deadline");
