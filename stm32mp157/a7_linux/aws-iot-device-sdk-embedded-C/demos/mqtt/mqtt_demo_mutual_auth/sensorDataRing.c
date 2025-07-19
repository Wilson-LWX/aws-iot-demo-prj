#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <unistd.h>
#include <fcntl.h>
#include <string.h>
#include <time.h>

#include "core_mqtt.h"
#include "sensorDataRing.h"

static int fd_M4 = 0;
static volatile __attribute__((aligned(4), section(".no_cache"))) RingBuffer sensorDataRing;
static RingBuffer* pSensorRingBuffer = NULL;
char sensorPayload[SENSOR_JSON_LEN];

extern int publishToMontorTopic( MQTTContext_t * pMqttContext, char * pSensorPayLoad);

// Ring buffer initialization
void ring_buffer_init(RingBuffer *rb) 
{
    rb->read_index = 0;
    rb->write_index = 0;
    rb->size = 0;

    printf("ring buffer initialzed\n");
}

int init_channels_M4()
{
    fd_M4 = open(RPMSG_DEVICE_M4, O_RDWR);

    if (fd_M4 < 0) 
    {
        perror("Failed to open rpmsg device");

        return -1;
    }

    pSensorRingBuffer = (RingBuffer *) &(sensorDataRing);
        
    memset((void *)pSensorRingBuffer, 0x00, sizeof(sensorDataRing));

    ring_buffer_init((RingBuffer *)pSensorRingBuffer);
            
    printf("init channel success and Wait for messages from M4...\n");

    return 0;
}

uint32_t bytes_to_uint32_bigE(uint8_t *buffer, size_t *index)
{
    uint32_t value = 0;
    size_t i = 0;

    for (i = 0; i < sizeof(uint32_t); i++) 
    {
        value = (value << 8) | buffer[*index];
        *index = (*index + 1) % BUFFER_SIZE;
    }
    return value;
}

uint32_t bytes_to_uint32_litE(uint8_t *buffer, size_t *index)
{
    uint32_t value = 0;
    size_t i = 0;
    
    // little Endian, the least the first
    for (i = 0; i < sizeof(uint32_t); i++)
    {
        value |= buffer[*index] << (8 * i);  
        *index = (*index + 1) % BUFFER_SIZE;
    }

    return value;
}

void print_received_data(const char *data, size_t len) 
{
    size_t i;
    
    // printf("Received %zu bytes of data:\n", len);

    for (i = 0; i < len; i++) 
    {
        printf("%02X", data[i]);  // Print each byte as a character
    }
    printf("\n");
}

int read_complete_frame(RingBuffer *ring, SensorRawData_t *frame) 
{
    size_t temp_read_index = ring->read_index;  // temp index
    uint32_t frame_head = 0, frame_head_index = 0;
    uint32_t temp_uint32 = 0;
    uint32_t calCheckSum = 0;
    size_t i = 0;

    // Loop through the buffer to find a valid frame header
    while (ring->size >= WHOLE_FRAME_LEN)
    {
        // Assemble the frame header byte by byte
        frame_head_index = temp_read_index;
        frame_head = bytes_to_uint32_litE(ring->buffer, &temp_read_index);

        // If the frame header matches
        if (frame_head == FRAME_HEADER)
        {
            // Parse each field of the data
            frame->frameNo = bytes_to_uint32_litE(ring->buffer, &temp_read_index);

            temp_uint32 = bytes_to_uint32_litE(ring->buffer, &temp_read_index);
            frame->temperature = *((float *) &temp_uint32);
            temp_uint32 = bytes_to_uint32_litE(ring->buffer, &temp_read_index);
            frame->gyro_x_vel =  *((float *) &temp_uint32);
            temp_uint32 = bytes_to_uint32_litE(ring->buffer, &temp_read_index);
            frame->gyro_y_vel =  *((float *) &temp_uint32);
            temp_uint32 = bytes_to_uint32_litE(ring->buffer, &temp_read_index);
            frame->gyro_z_vel =  *((float *) &temp_uint32);
            
            frame->checkSum = bytes_to_uint32_litE(ring->buffer, &temp_read_index);

            printf("frameNo:%u, temp:%.2f, gyro_x:%.2f, gyro_y%.2f, gyro_z:%.2f, checkSum:%u \n",\
                   frame->frameNo, frame->temperature, frame->gyro_x_vel, frame->gyro_y_vel, frame->gyro_z_vel, frame->checkSum);

            // Validate the frame data
            calCheckSum = 0;
            for(i=0; i<WHOLE_FRAME_LEN-4; i++)
            {
                calCheckSum ^= (uint8_t)*((uint8_t *)(ring->buffer + ((frame_head_index + i)% BUFFER_SIZE) ));
            }
            
            //if (validate_frame(frame)) 
            if(calCheckSum == frame->checkSum)
            {
                // If the frame passes validation, update the pointer and discard the processed data
                ring->read_index = temp_read_index;
                ring->size -= sizeof(SensorRawData_t);  // reduce size of buffered data

                printf("Valid frame with new read_index:%u, ringSize:%u \n", temp_read_index, ring->size);

                return 1;  // Successfully read a complete frame
            }
            else
            {
                // If the checksum fails, print a warning and skip this frame
                printf("Invalid frame at index %zu, skipping...\n", temp_read_index);                

                // Skip the current 4-byte frame header and continue searching for the next header
                temp_read_index = (frame_head_index + FRAME_HEADER_SIZE) % BUFFER_SIZE;
                ring->size -= FRAME_HEADER_SIZE;  // reduce size of buffered data
                //ring->read_index += FRAME_HEADER_SIZE;
                ring->read_index = temp_read_index;
                continue;  // Skip this frame and continue to search
            }
        }

        // If the header doesn't match, continue searching for next possible header
        frame_head = 0;  // Reset frame header
        temp_read_index = (frame_head_index + 1) % BUFFER_SIZE;
        ring->size -= 1;  // reduce size of buffered data
        ring->read_index = temp_read_index;
    }

    // No complete frame founds
    return 0;  // Wait for more data
}

uint32_t calculate_checksum(SensorRawData_t *frame)
{
    uint32_t checksum = 0;
    size_t i = 0;

    // XOR each byte to calculate the checksum
    uint8_t *byte_ptr = (uint8_t *)frame;

    for (i = 0; i < sizeof(SensorRawData_t)-4; i++) 
    {
        checksum ^= byte_ptr[i];
    }

    return checksum;
}

int validate_frame(SensorRawData_t *frame) 
{
    uint32_t calCheckSum = 0;

    // Calculate and verify checksum
    calCheckSum = calculate_checksum(frame);

    if ( frame->checkSum == calCheckSum ) 
    {
        return 1;
    }

    printf("Frame validation fail with expected checkSum:0x%lx, peer checkSum:0x%lx \n", calCheckSum, frame->checkSum);
    return 0;
}

void encode_data_for_cloud(char *sensorPayload, SensorRawData_t *frame) 
{
    float temperature, humidity, light;
    float gyro_x, gyro_y, gyro_z;
    
    uint32_t ts = (uint32_t)time(NULL); 
    
    //Use assumed values for humidity and illumination
    humidity = 0.55;
    light = 209.00;

    //add some random noise to smooth graph, just for display purpose
    float noise_t = ((rand() % 100) - 50) / 10.0f;  // -5.0 to +4.9
    float noise_h = ((rand() % 20) - 10) / 100.0f;    // -0.10 to +0.09
    float noise_gx = ((rand() % 100) - 50) / 100.0f; // -0.5 to +0.49
    float noise_gy = ((rand() % 100) - 50) / 100.0f; // -0.5 to +0.49
    float noise_gz = ((rand() % 100) - 50) / 100.0f; // -0.5 to +0.49
    float noise_light = ((rand() % 100) - 50) / 10.0f;  // -5.0 to +4.9

    temperature = frame->temperature + noise_t;
    humidity = humidity + noise_h;
    gyro_x = frame->gyro_x_vel + noise_gx;
    gyro_y = frame->gyro_y_vel + noise_gy;
    gyro_z = frame->gyro_z_vel + noise_gz;
    light  = light + noise_light;

    // snprintf(sensorPayload, 256,
    //          "{\"frmNo\": %u, \"ts\": %u, \"gyro_x\": %.2f, \"gyro_y\": %.2f, "
    //          "\"gyro_z\": %.2f, \"temperature\": %.2f, \"humidity\": %.2f, \"light\": %.2f}",
    //          frame->frameNo, ts, frame->gyro_x_vel, frame->gyro_y_vel,
    //          frame->gyro_z_vel, frame->temperature, 0.63, 189.50);
    
    snprintf(sensorPayload, 256,
             "{\"frmNo\": %u, \"ts\": %u, \"gyro_x\": %.2f, \"gyro_y\": %.2f, "
             "\"gyro_z\": %.2f, \"temperature\": %.2f, \"humidity\": %.2f, \"light\": %.2f}",
             frame->frameNo, ts, gyro_x, gyro_y,
             gyro_z, temperature, humidity, light);

    printf("sensor payload with JSON: %s\n", sensorPayload);
}

void simulate_sensor_data(MQTTContext_t * pMqttContext)
{    
    SensorRawData_t frame;
    char *pSensorPayload = sensorPayload;

    frame.frameHead = FRAME_HEADER;
    frame.frameNo = 0;
    frame.temperature = 20.0f;
    frame.gyro_x_vel = 1.0f;
    frame.gyro_y_vel = 2.0f;
    frame.gyro_z_vel = 3.0f;
    frame.checkSum = 0;

    encode_data_for_cloud(pSensorPayload, &frame);
    publishToMontorTopic(pMqttContext, pSensorPayload);

    return;
}

int gather_sensor_data(MQTTContext_t * pMqttContext, char * pSensorPayload)
{
    SensorRawData_t frame;
    size_t maxBytesToRead = BUFFER_SIZE - pSensorRingBuffer->write_index;  // maximum buffer size to store data
    ssize_t bytes_read = read(fd_M4, pSensorRingBuffer->buffer + pSensorRingBuffer->write_index, maxBytesToRead);
    int ret = 0;

    printf("Returned %d bytes of data, maximum expected bytes%d \n", bytes_read, maxBytesToRead);    

    if (bytes_read > 0) 
    {
        print_received_data(pSensorRingBuffer->buffer + pSensorRingBuffer->write_index, bytes_read);

        // update write_index and size
        pSensorRingBuffer->write_index = (pSensorRingBuffer->write_index + bytes_read) % BUFFER_SIZE;
        pSensorRingBuffer->size += bytes_read;

        // Read and process complete frame
        //while (read_complete_frame(pSensorRingBuffer, &frame)) 
        if (read_complete_frame(pSensorRingBuffer, &frame)) 
        {
            encode_data_for_cloud(pSensorPayload, &frame);

            publishToMontorTopic(pMqttContext, pSensorPayload);

            ret = 1;

            //break;  //one frame each time for ts sampling
        }
    }
    else if(bytes_read == 0)
    {
        printf("NO data returned from M4 channel \n");
    }
    else
    {
        perror("read failed");
        ret = -1;
    }

    return ret;
}
