#include<Wire.h>

//Endereço I2C do sensor (de acordo com o fabricante)
const int MPU = 0x68;
static unsigned long contador = 0;

//variáveis para armazenar os dados do sensor
float a_x,a_y,a_z,temperatura,Gyrx,Gyry,Gyrz;



void setup() {
  Serial.begin(115200); // se atentar a taxa de baud para aumentar os Hz dos dados (E no serial monitor deveestar igual)
  //inicializando o módulo MPU
  //Serial.println("SETUP EXECUTADO");
  Wire.begin();
  Wire.beginTransmission(MPU);
  if(Wire.endTransmission() == 0){
   // Serial.println("MPU conectado");
    delay(10000);
  }

  else{
    Serial.println("Erro MPU");
  }
  Wire.beginTransmission(MPU);
  Wire.write(0x6B);
  Wire.write(0);
  Wire.endTransmission(true);


  //CONFIGURAÇÃO do giroscópio
  /*
    Wire.write(0b00000000); // fundo de escala em +/-250°/s
    Wire.write(0b00001000); // fundo de escala em +/-500°/s
    Wire.write(0b00010000); // fundo de escala em +/-1000°/s
    Wire.write(0b00011000); // fundo de escala em +/-2000°/s
  */
  Wire.beginTransmission(MPU);
  Wire.write(0x1B);
  Wire.write(0b00011000);
  Wire.endTransmission(true);

  
   //CONFIGURAÇÃO do acelerômetro
  /*
    Wire.write(0b00000000); // fundo de escala em +/-2g
    Wire.write(0b00001000); // fundo de escala em +/-4g
    Wire.write(0b00010000); // fundo de escala em +/-8g
    Wire.write(0b00011000); // fundo de escala em +/-16g
  */
  Wire.beginTransmission(MPU);
  Wire.write(0x1C);
  Wire.write(0b00011000);//a depender do fundo de escala requerido (16)
  Wire.endTransmission(true);

}




void loop() {
  Wire.beginTransmission(MPU);
  Wire.write(0x3B);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU,14,true);//solicita os dados do sensor
  //Serial.print("Bytes recebidos: ");
  //Serial.println(Wire.available());DEBUG

  //aRMANZENDO OS VALORES NAS VARIÁVEIS CORRESPONDENTES(NOTE QUE ELE MANDA OS VALORES FLOAT INICIALIZADOS). 
  //Os registros estão presentes na referência da InvenSense(MPU REGISTER MAP.PDF)
  if (Wire.available() >= 14){
    a_x = Wire.read() << 8 | Wire.read();  //0x3B (ACCEL_XOUT_H) & 0x3C (ACCEL_XOUT_L)
    a_y = Wire.read() << 8 | Wire.read(); //0x3D (ACCEL_YOUT_H) & 0x3E (ACCEL_YOUT_L)
    a_z = Wire.read() << 8 | Wire.read();  //0x3F (ACCEL_ZOUT_H) & 0x40 (ACCEL_ZOUT_L)
    temperatura = Wire.read() << 8 | Wire.read(); //0x41 (TEMP_OUT_H) & 0x42 (TEMP_OUT_L)
    Gyrx = Wire.read() << 8 | Wire.read();  //0x43 (GYRO_XOUT_H) & 0x44 (GYRO_XOUT_L)
    Gyry = Wire.read() << 8 | Wire.read();  //0x45 (GYRO_YOUT_H) & 0x46 (GYRO_YOUT_L)
    Gyrz = Wire.read() << 8 | Wire.read();  //0x47 (GYRO_ZOUT_H) & 0x48 (GYRO_ZOUT_L)
  }

  //Parte interessante: Imprimeindo na serial os valores que o sensor recebe
  /*
  Os vlaores recebidos (SEGUNDO O MPU DATASHEET) devem ser dividos pelos respectivos considerando o fundo de escala escolhido
  Acelerômetro
  -2g = (16384)
  -4g = (8192)
  -8g = (4096)
  -16g = (2048)

  Giroscópio
  -250°/s = 131
  -500°/s = 65,6
  -1000°/s = 32,8
  -2000°/s = 16,4
  */

  contador++;
  
  
  Serial.print(contador);
  Serial.print(",");

  Serial.print(micros());
  /
  Serial.print(",");

  Serial.print(a_x/2048);
  Serial.print(",");

  Serial.print(a_y/2048);
  Serial.print(",");

  Serial.print(a_z/2048);
  
  
  Serial.print(",");

  Serial.print(Gyrx/16.4);
  Serial.print(",");

  Serial.print(Gyry/16.4);
  Serial.print(",");

  Serial.println(Gyrz/16.4);
  
  
  
}
