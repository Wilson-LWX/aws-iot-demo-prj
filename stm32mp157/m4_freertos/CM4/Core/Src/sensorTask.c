/**
  ******************************************************************************
  * @file    sensorTask.c
  * @author  Wilson
  * @brief   Task definition for sensor data collection and report
  *          1) report sensor data to AWS cloud via A7
  *          2) can adjust report period dynamically
  *
  *
  ******************************************************************************
  */
#include "cmsis_os.h"
#include "stm32mp1xx_it.h"
#include "FreeRTOS.h"
#include "task.h"
#include "openamp.h"
#include "icm_20608g.h"

#define SENSOR_OUTPUT_QUE_LEN 8
__attribute__((aligned(4), section(".no_cache"))) ICM_Data_t outputData[SENSOR_OUTPUT_QUE_LEN];

QueueHandle_t IcmQueue;
#define ICM_QUEUE_LEN 16

static struct rpmsg_endpoint M4_Ept;
uint32_t samplePeriod = 1;  //default 1S
boolean reportEnabled = false;

static uint32_t frameNo = 0;
static uint8_t queIndex = 0;

//static char replyMsgBuf[32];

extern volatile ICM_Gyro_State Icm_Gyro_State;

void ICM_ParseRawData(ICM_Data_t* out, const uint8_t* raw_buf);

extern void ICM_TxRx_Callback(void);

// callback for IPCC between A7<->M4
int icm_rx_callback(struct rpmsg_endpoint *ept, void *data, size_t len, uint32_t src, void *priv)
{
	unsigned int newPeriod = 0;
	// command string
	char *inputCmd = (char *)data;

	if (strcmp(inputCmd, "START") == 0)
	{
		if(Icm_Gyro_State != ICM_GYRO_STATE_ON)
		{
			ICM_Init();
			samplePeriod = 1;
			queIndex = 0;
			frameNo = 0;
			Icm_Gyro_State = ICM_GYRO_STATE_ON;

//			sprintf(replyMsgBuf, "Icm_Gyro_State is %d \n", Icm_Gyro_State);
//			rpmsg_send(&M4_Ept, replyMsgBuf, strlen(replyMsgBuf));

			printf("Gyro is started \n");
		}
		else
		{
			printf("Gyro is already in ICM_GYRO_STATE_ON state \n");
		}
	}
	else if (strcmp(inputCmd, "STOP") == 0)
	{
		ICM_Disable();
		Icm_Gyro_State = ICM_GYRO_STATE_OFF;

//		sprintf(replyMsgBuf, "Icm_Gyro_State is %d \n", Icm_Gyro_State);
//		rpmsg_send(&M4_Ept, replyMsgBuf, strlen(replyMsgBuf));
	}
	if (strncmp(inputCmd, "SAMPERIOD:", 10) == 0)
	{
		// set up sampling period
		if (sscanf(inputCmd + 10, "%d", &newPeriod) == 1)
		{
			if(samplePeriod > 60) //maxmimu 60S
				samplePeriod = 60;
			else
				samplePeriod = newPeriod;

			printf("Setting sample period to: %lu seconds\n", samplePeriod);
		}
		else
		{
			printf("Invalid sample period format.\n");
		}
	}
	else if (strcmp(inputCmd, "RESTART") == 0)
	{
		ICM_Init();
		queIndex = 0;
		frameNo = 0;
		Icm_Gyro_State = ICM_GYRO_STATE_ON;
	}
//	else if (strcmp(inputCmd, "RELEASE") == 0)
//	{
//		// 执行 RELEASE 命令的操作
//
//		icm_Gyro_State = ICM_GYRO_STATE_NULL;
//	}
	else if(strcmp(inputCmd, "DEBUG") == 0)
	{
		printf("M4 receives msg from A7: %.*s \n", (int)len, (char *)data);

		//sprintf(replyMsgBuf, "I am from M4！\n");
		//rpmsg_send(&M4_Ept, replyMsgBuf, strlen(replyMsgBuf));
	}
	else
	{
		// Unknown command and trace
		printf("Unknown command: %s\n", inputCmd);
	}

	return 0;
}

uint32_t calculate_checksum(ICM_Data_t *frame)
{
    uint32_t checksum = 0;

    uint8_t *byte_ptr = (uint8_t *)frame;

    for (size_t i = 0; i < sizeof(ICM_Data_t) - 4; i++) {
        checksum ^= byte_ptr[i];  // bytes XOR
    }

    return checksum;
}

#ifdef GYRO_MODE_INT
void SensorTask(void const *argument)
{
	static ICM_Raw_Data_t rawData;

	OPENAMP_init_ept(&M4_Ept);
	OPENAMP_create_endpoint(&M4_Ept,
					 //"rpmsg-openamp-demo-channel", // match name definition on A7 side
					 //"rpmsg-client-sample",
					 "rpmsg-tty-channel",
					 RPMSG_ADDR_ANY,
					 icm_rx_callback,
					 NULL);

	ICM_Init();
	queIndex = 0;
	frameNo = 0;

	IcmQueue = xQueueCreate(ICM_QUEUE_LEN, sizeof(ICM_Raw_Data_t));

    for (;;)
    {
    	if( Icm_Gyro_State == ICM_GYRO_STATE_ON )
    	{
   	        if (xQueueReceive(IcmQueue, (void *)&rawData, 0) == pdTRUE)
   	        {
   	            ICM_ParseRawData((ICM_Data_t *)(&outputData), (uint8_t *)&rawData);

   	            // printf("Temp: %.2f°C, Gyro: X=%d Y=%d Z=%d\n",
   	            //         outputData.temperature, outputData.gyro_x_vel, outputData.gyro_y_vel, outputData.gyro_z_vel);

   				outputData[queIndex].frameHead = FRAME_HEAD;
   				outputData[queIndex].frameNo = frameNo;

   				outputData[queIndex].checkSum = calculate_checksum(&outputData[queIndex]);

   				OPENAMP_check_for_message();

   				rpmsg_send(&M4_Ept, &outputData[queIndex], sizeof(ICM_Data_t));

   				frameNo += 1;
   				queIndex = (queIndex + 1) % SENSOR_OUTPUT_QUE_LEN;
   	        }

    		OPENAMP_check_for_message();

			osDelay(1000 * samplePeriod); //adjustable report period
    	}
    	else
    	{
    		OPENAMP_check_for_message();

    		osDelay(100);
    	}
    }
}
#else
void SensorTask(void const *argument)
{
	/* USER CODE BEGIN 5 */
	OPENAMP_init_ept(&M4_Ept);

	OPENAMP_create_endpoint(&M4_Ept,
					 //"rpmsg-openamp-demo-channel", // match name definition on A7 side
					 //"rpmsg-client-sample",
					 "rpmsg-tty-channel",
					 RPMSG_ADDR_ANY,
					 icm_rx_callback,
					 NULL);

	ICM_Init();
	queIndex = 0;
	frameNo = 0;

    for (;;)
    {
    	if( Icm_Gyro_State == ICM_GYRO_STATE_ON )
    	{
			outputData[queIndex].frameHead = FRAME_HEAD;
			outputData[queIndex].frameNo = frameNo;

			ICM_ReadGyroAccel(&outputData[queIndex]);

			outputData[queIndex].checkSum = calculate_checksum(&outputData[queIndex]);

			OPENAMP_check_for_message();

			rpmsg_send(&M4_Ept, &outputData[queIndex], sizeof(ICM_Data_t));

    		OPENAMP_check_for_message();

			frameNo += 1;
			queIndex = (queIndex + 1) % SENSOR_OUTPUT_QUE_LEN;

			osDelay(1000 * samplePeriod); //adjustable report period
    	}
    	else
    	{
    		OPENAMP_check_for_message();

    		osDelay(100);
    	}
    }
}
#endif
