#include <stdio.h>
#include <stdint.h>
#include <string.h>

#define RPMSG_DEVICE_M4 "/dev/ttyRPMSG0"
#define BUFFER_SIZE  512  // ring buffer bytes to hold M4 reports
#define FRAME_HEADER  0x5E7FF7E5
#define FRAME_HEADER_SIZE  4
#define SENSOR_JSON_LEN 256

typedef struct
{
    uint32_t frameHead;      // framee head fixed as 0x5E7FF7E5
    uint32_t frameNo;        // frame number
    float temperature;       // temperature from sensors
    float gyro_x_vel;        // gyroscope X vel
    float gyro_y_vel;        // gyroscope Y vel
    float gyro_z_vel;        // gyroscope Z vel
    uint32_t checkSum;       // XOR of all fields except checkSum
} SensorRawData_t;

#define WHOLE_FRAME_LEN sizeof(SensorRawData_t)

typedef struct
{
    uint8_t buffer[BUFFER_SIZE];  // ring buffer
    size_t write_index;           // index to write
    size_t read_index;            // index to read 
    size_t size;                  // total number of bytes in the ring buffer
} RingBuffer;

// the struct for reporting to AWS IoT core
typedef struct 
{
    uint32_t frameNo;    
    uint32_t timestamp;

    //samping data from gyro
    float temperature;
    float gyro_x_vel;
    float gyro_y_vel;
    float gyro_z_vel;

    //using simulation
    float lum_value;
    float humidity;
}SensorData_t;
