/*
 * icm_20608g.c
 *
 *  Created on: Jun 7, 2025
 *  Author: wison
 */
#include "icm_20608g.h"
#include "spi.h"
#include "stm32mp1xx_it.h"
#include "FreeRTOS.h"
#include "queue.h"

#define Dummy_Byte				(0xFF)

uint8_t  gyroTxBuf[GYRO_EXC_BYTE_LEN+1];
uint8_t  gyroRxBuf[GYRO_EXC_BYTE_LEN+1];

//offset used to calibration of gyro
static int16_t  gyroOffset_X = 0, gyroOffset_Y = 0, gyroOffset_Z = 0;

extern QueueHandle_t IcmQueue;
volatile ICM_Gyro_State Icm_Gyro_State = ICM_GYRO_STATE_NULL;


uint8_t ICM_RW_Register(uint8_t reg, uint8_t data)
{
	uint16_t rxdata = 0;
	uint16_t txdata = (data<<8) | reg;

	if(HAL_SPI_TransmitReceive(&hspi5, (uint8_t*)&txdata, (uint8_t*)&rxdata, sizeof(rxdata), 300) != HAL_OK)
	{
		Error_Handler();
	}

	return (rxdata>>8);
}


void ICM_Init(void)
{
	uint8_t ret;

	// reset ICM
	ICM_RW_Register(ICM_PWM_MGMT_1 | ICM_WRITE, 0x80);
	HAL_Delay(50);

	// select PLL
	ICM_RW_Register(ICM_PWM_MGMT_1 | ICM_WRITE, 0x01);
	HAL_Delay(50);

	// get device ID
	ret = ICM_RW_Register(ICM_WHO_AM_I | ICM_READ, Dummy_Byte);
	printf("\rICM ID: 0x%x\n", ret);

	//set up 100Hz sampling rate
	ICM_RW_Register(ICM_SMPLRT_DIV | ICM_WRITE, 9);

	// 2000dps
	ICM_RW_Register(ICM_GYRO_CONFIG | ICM_WRITE, 0x18);
	// accelerator 16G
	ICM_RW_Register(ICM_ACCEL_CONFIG | ICM_WRITE, 0x18);

	// gryo LPF 20Hz
	ICM_RW_Register(ICM_CONFIG | ICM_WRITE, 0x04);
	// gyro acc LPF 21.2Hz
	ICM_RW_Register(ICM_ACCEL_CONFIG_2 | ICM_WRITE, 0x04);

	// enable all gryo axles
	ICM_RW_Register(ICM_PWM_MGMT_1 | ICM_WRITE, 0x00);

	// disable low power
	ICM_RW_Register(ICM_LP_MODE_CFG | ICM_WRITE, 0x00);

	// disable FIFO
	ICM_RW_Register(ICM_FIFO_EN | ICM_WRITE, 0x00);

	//samping 10 times to get calibration value
	ICM_GyroCalibrateOffset(10);

#ifdef GYRO_MODE_INT
	//Enable Gyro interrupt txRx
	gyroTxBuf[0] = ICM_TEMP_OUT_H | 0x80;  // 从 ICM_TEMP_OUT_H 开始读
	memset(&gyroTxBuf[1], Dummy_Byte, GYRO_EXC_BYTE_LEN);  //dummy bytes initialization
	//HAL_GPIO_WritePin(GPIOX_CS, PIN_CS, 0);
	HAL_SPI_TransmitReceive_IT(&hspi5, gyroTxBuf, gyroRxBuf, GYRO_EXC_BYTE_LEN+1);
	//HAL_GPIO_WritePin(GPIOX_CS, PIN_CS, 1);
	HAL_Delay(50);
#endif

	return;
}

void ICM_Disable(void)
{
	ICM_RW_Register(ICM_PWM_MGMT_1 | ICM_WRITE, 0x40);

    printf("Gyro sampling stopped and device is in sleep mode\n");

    return;
}

#ifdef GYRO_MODE_INT
void HAL_SPI_TxRxCpltCallback(SPI_HandleTypeDef *hspi)
{
	if (hspi->Instance == SPI5)
	{
	    BaseType_t xHigherPriorityTaskWoken = pdFALSE;
	    xQueueSendFromISR(IcmQueue, gyroRxBuf, &xHigherPriorityTaskWoken);

	    portYIELD_FROM_ISR(xHigherPriorityTaskWoken);
	}

	return;
}

void ICM_TxRx_Callback(void)
{
	gyroTxBuf[0] = ICM_TEMP_OUT_H | 0x80;  //from ICM_TEMP_OUT_H
	memset(&gyroTxBuf[1], Dummy_Byte, GYRO_EXC_BYTE_LEN);  //dummy bytes initialization

	HAL_SPI_TransmitReceive_IT(&hspi5, gyroTxBuf, gyroRxBuf, GYRO_EXC_BYTE_LEN+1);

	return;
}
#endif

void ICM_ParseRawData(ICM_Data_t* out, const uint8_t* raw_buf)
{
    if (out == NULL || raw_buf == NULL) return;

    out->temperature = ((int16_t)((raw_buf[1] << 8) | raw_buf[2]))/326.8 + 25.0;

    out->gyro_x_vel  = ((int16_t)((raw_buf[3] << 8) | raw_buf[4]) - gyroOffset_X)/16.4;
    out->gyro_y_vel  = ((int16_t)((raw_buf[5] << 8) | raw_buf[6]) - gyroOffset_Y)/16.4;
    out->gyro_z_vel  = ((int16_t)((raw_buf[7] << 8) | raw_buf[8]) - gyroOffset_Z)/16.4;

    return;
}

void ICM_ReadGyroRaw(int16_t* gx, int16_t* gy, int16_t* gz)
{
	gyroTxBuf[0] = ICM_GYRO_XOUT_H | 0x80;  //initialize CMD byte
    memset((void *)&gyroTxBuf[1], 0xFF, 6);

	if(HAL_SPI_TransmitReceive(&hspi5, gyroTxBuf, gyroRxBuf, 7, 100) != HAL_OK)
	{
		Error_Handler();
	}

    *gx = (int16_t)((gyroRxBuf[1] << 8) | gyroRxBuf[2]);
    *gy = (int16_t)((gyroRxBuf[3] << 8) | gyroRxBuf[4]);
    *gz = (int16_t)((gyroRxBuf[5] << 8) | gyroRxBuf[6]);

    return;
}

void ICM_GyroCalibrateOffset(uint16_t sample_count)
{
    int32_t sum_x = 0, sum_y = 0, sum_z = 0;
    int16_t gx, gy, gz;

    for (uint16_t i = 0; i < sample_count; ++i)
    {
        ICM_ReadGyroRaw(&gx, &gy, &gz);  // read raw angular velocity

        sum_x += gx;
        sum_y += gy;
        sum_z += gz;

        HAL_Delay(2);
    }

    gyroOffset_X = (float)sum_x / sample_count;
    gyroOffset_Y = (float)sum_y / sample_count;
    gyroOffset_Z = (float)sum_z / sample_count;

    return;
}

#ifdef GYRO_MODE_POLL
void ICM_ReadGyroAccel(ICM_Data_t *data)
{
	int16_t temp = 0;
	float temp_value = 0;
	uint8_t temp_h = 0, temp_l = 0;

	int16_t xa = 0, ya = 0, za = 0;
	float xa_act = 0, ya_act = 0, za_act = 0;
	uint8_t xa_l = 0, ya_l = 0, za_l = 0;
	uint8_t xa_h = 0, ya_h = 0, za_h = 0;

	int16_t xg = 0, yg = 0, zg = 0;
	float xg_act = 0, yg_act = 0, zg_act = 0;
	uint8_t xg_l = 0, yg_l = 0, zg_l = 0;
	uint8_t xg_h = 0, yg_h = 0, zg_h = 0;

	temp_l = ICM_RW_Register(ICM_TEMP_OUT_L | ICM_READ, Dummy_Byte);
	temp_h = ICM_RW_Register(ICM_TEMP_OUT_H | ICM_READ, Dummy_Byte);
	temp = (temp_h<<8) | temp_l;
	temp_value = (temp - 25)/326.8 + 25;

	xa_l = ICM_RW_Register(ICM_ACCEL_XOUT_L | ICM_READ, Dummy_Byte);
	xa_h = ICM_RW_Register(ICM_ACCEL_XOUT_H | ICM_READ, Dummy_Byte);
	ya_l = ICM_RW_Register(ICM_ACCEL_YOUT_L | ICM_READ, Dummy_Byte);
	ya_h = ICM_RW_Register(ICM_ACCEL_YOUT_H | ICM_READ, Dummy_Byte);
	za_l = ICM_RW_Register(ICM_ACCEL_ZOUT_L | ICM_READ, Dummy_Byte);
	za_h = ICM_RW_Register(ICM_ACCEL_ZOUT_H | ICM_READ, Dummy_Byte);
	xa = xa_l + (xa_h<<8);	xa_act = xa / 2048.0;
	ya = ya_l + (ya_h<<8);	ya_act = ya / 2048.0;
	za = za_l + (za_h<<8);	za_act = za / 2048.0;

	xg_l = ICM_RW_Register(ICM_GYRO_XOUT_L | ICM_READ, Dummy_Byte);
	xg_h = ICM_RW_Register(ICM_GYRO_XOUT_H | ICM_READ, Dummy_Byte);
	yg_l = ICM_RW_Register(ICM_GYRO_YOUT_L | ICM_READ, Dummy_Byte);
	yg_h = ICM_RW_Register(ICM_GYRO_YOUT_H | ICM_READ, Dummy_Byte);
	zg_l = ICM_RW_Register(ICM_GYRO_ZOUT_L | ICM_READ, Dummy_Byte);
	zg_h = ICM_RW_Register(ICM_GYRO_ZOUT_H | ICM_READ, Dummy_Byte);
	xg = xg_l + (xg_h<<8);	xg_act = xg / 16.4;
	yg = yg_l + (yg_h<<8);	yg_act = yg / 16.4;
	zg = zg_l + (zg_h<<8);	zg_act = zg / 16.4;

	data->temperature = temp_value;
	data->gyro_x_vel = (xg - gyroOffset_X)/16.4;
	data->gyro_y_vel = (xg - gyroOffset_Y)/16.4;
	data->gyro_z_vel = (xg - gyroOffset_Z)/16.4;

//	printf("\r-----------------------------------\n");
//
//	printf("\rTemperature Original value: 0x%x \n", temp);
//	printf("\rTemperature Converted value: %.2f\n", temp_value);
//	printf("\r\n");
//	printf("\rAccelerometer Original value: xa:0x%x ya:0x%x za:0x%x \n", xa, ya, za);
//	printf("\rAccelerometer Converted value: xa_act:%.2fg ya_act:%.2fg za_act:%.2fg \n", xa_act, ya_act, za_act);
//	printf("\r\n");
//	printf("\rGyroscope Original value: xg:0x%x yg:0x%x zg:0x%x \n", xg, yg, zg);
//	printf("\rGyroscope Converted value: xg_act:%.2fdeg/s yg_act:%.2fdeg/s zg_act:%.2fdeg/s \n", xg_act, yg_act, zg_act);
//
//	printf("\r-----------------------------------\n");

	return;
}
#endif
