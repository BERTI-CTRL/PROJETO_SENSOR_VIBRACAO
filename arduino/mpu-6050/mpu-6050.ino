// Importa a biblioteca Wire, usada pelo Arduino como mestre do barramento I2C.
#include<Wire.h>

// Endereco I2C usado pelo firmware; 0x68 pressupoe que o pino AD0 do MPU6050 esteja em nivel baixo.
const int MPU = 0x68;
// Mantem a sequencia das amostras entre chamadas de loop(); unsigned long volta a zero ao exceder sua faixa.
static unsigned long contador = 0;

// Armazena em ponto flutuante as palavras lidas: tres aceleracoes, temperatura e tres velocidades angulares.
float a_x,a_y,a_z,temperatura,Gyrx,Gyry,Gyrz;



// Executa uma vez apos a inicializacao ou reinicializacao da placa.
void setup() {
  // Abre a serial a 230400 baud; o receptor precisa usar exatamente a mesma taxa.
  Serial.begin(230400);

  // Inicializa o controlador I2C da placa com os pinos e a frequencia padrao da implementacao de Wire.
  Wire.begin();

  // Inicia uma transmissao apenas para testar se algum dispositivo reconhece o endereco 0x68.
  Wire.beginTransmission(MPU);
  // O retorno zero indica ACK no endereco; nao confirma por si so a identidade do componente.
  if(Wire.endTransmission() == 0){
    // Quando ha resposta, conserva a espera historica de 10 segundos antes de configurar e amostrar.
    delay(10000);
  }

  // Trata a ausencia de ACK no teste de endereco.
  else{
    // Envia uma linha livre de diagnostico; o leitor Python a rejeita por nao ter os oito campos do protocolo.
    Serial.println("Erro MPU");
  }

  // Abre uma escrita no MPU6050 para acordar e definir a fonte de clock.
  Wire.beginTransmission(MPU);
  // Seleciona o registrador PWR_MGMT_1, endereco 0x6B.
  Wire.write(0x6B);
  // Escreve zero: limpa SLEEP e mantem CLKSEL=0, isto e, oscilador interno de 8 MHz.
  Wire.write(0);
  // Encerra a escrita enviando uma condicao STOP.
  Wire.endTransmission(true);


  /* Alternativas documentais de fundo de escala do giroscopio; somente 0b00011000 abaixo e executado.
    Wire.write(0b00000000); // fundo de escala em +/-250 graus/s
    Wire.write(0b00001000); // fundo de escala em +/-500 graus/s
    Wire.write(0b00010000); // fundo de escala em +/-1000 graus/s
    Wire.write(0b00011000); // fundo de escala em +/-2000 graus/s
  */
  // Inicia a escrita da configuracao do giroscopio.
  Wire.beginTransmission(MPU);
  // Seleciona GYRO_CONFIG, endereco 0x1B.
  Wire.write(0x1B);
  // Define FS_SEL=3 (bits 4:3 em 11): faixa de +/-2000 graus/s e self-test desativado.
  Wire.write(0b00011000);
  // Confirma a configuracao com uma condicao STOP.
  Wire.endTransmission(true);


  /* Alternativas documentais de fundo de escala do acelerometro; somente 0b00011000 abaixo e executado.
    Wire.write(0b00000000); // fundo de escala em +/-2g
    Wire.write(0b00001000); // fundo de escala em +/-4g
    Wire.write(0b00010000); // fundo de escala em +/-8g
    Wire.write(0b00011000); // fundo de escala em +/-16g
  */
  // Inicia a escrita da configuracao do acelerometro.
  Wire.beginTransmission(MPU);
  // Seleciona ACCEL_CONFIG, endereco 0x1C.
  Wire.write(0x1C);
  // Define AFS_SEL=3 (bits 4:3 em 11): faixa de +/-16g e self-test desativado.
  Wire.write(0b00011000);
  // Confirma a configuracao com uma condicao STOP.
  Wire.endTransmission(true);

}




// Repete continuamente uma leitura em bloco e a transmissao de uma amostra pela serial.
void loop() {
  // Inicia a fase de selecao do primeiro registrador que sera lido.
  Wire.beginTransmission(MPU);
  // Aponta para ACCEL_XOUT_H, endereco inicial 0x3B do bloco de medicoes.
  Wire.write(0x3B);
  // false encerra sem STOP para que a leitura seguinte use uma condicao repeated START.
  Wire.endTransmission(false);
  // Solicita 14 bytes consecutivos e envia STOP ao final: aceleracao, temperatura e giroscopio.
  Wire.requestFrom(MPU,14,true);

  // Exige o bloco completo antes de consumir bytes ou produzir uma linha serial.
  if (Wire.available() < 14) {
    // Abandona esta iteracao; o contador nao avanca e valores antigos nao sao retransmitidos.
    return;
  }

  // Reune os bytes alto e baixo de ACCEL_XOUT_X e atribui o resultado a float.
  a_x = Wire.read() << 8 | Wire.read();
  // Reune os bytes alto e baixo de ACCEL_XOUT_Y.
  a_y = Wire.read() << 8 | Wire.read();
  // Reune os bytes alto e baixo de ACCEL_XOUT_Z.
  a_z = Wire.read() << 8 | Wire.read();
  // Consome TEMP_OUT_H/L para preservar o alinhamento do burst; este valor nao e enviado no protocolo atual.
  temperatura = Wire.read() << 8 | Wire.read();
  // Reune os bytes alto e baixo de GYRO_XOUT_X.
  Gyrx = Wire.read() << 8 | Wire.read();
  // Reune os bytes alto e baixo de GYRO_XOUT_Y.
  Gyry = Wire.read() << 8 | Wire.read();
  // Reune os bytes alto e baixo de GYRO_XOUT_Z.
  Gyrz = Wire.read() << 8 | Wire.read();

  /*
  Cada registro de eixo e uma palavra de 16 bits em complemento de dois. O codigo recompoe os bytes
  sem conversao explicita para int16_t antes de atribuir a float; essa interpretacao depende do tamanho
  de int na plataforma Arduino e merece validacao se a placa-alvo mudar.

  Sensibilidades nominais por fundo de escala do acelerometro:
  +/-2g = 16384 LSB/g; +/-4g = 8192 LSB/g; +/-8g = 4096 LSB/g; +/-16g = 2048 LSB/g.

  Sensibilidades nominais por fundo de escala do giroscopio:
  +/-250 graus/s = 131 LSB/(grau/s); +/-500 = 65,5; +/-1000 = 32,8; +/-2000 = 16,4.
  */

  // Conta somente amostras que chegaram com os 14 bytes completos.
  contador++;


  // Campo 1/8: numero sequencial da amostra.
  Serial.print(contador);
  // Delimita o campo seguinte com virgula.
  Serial.print(",");

  // Campo 2/8: instante local do Arduino em microssegundos; micros() tambem sofre overflow.
  Serial.print(micros());

  // Delimita o campo seguinte com virgula.
  Serial.print(",");

  // Campo 3/8: aceleracao X em g, usando a sensibilidade nominal da faixa de +/-16g.
  Serial.print(a_x/2048);
  // Delimita o campo seguinte com virgula.
  Serial.print(",");

  // Campo 4/8: aceleracao Y em g.
  Serial.print(a_y/2048);
  // Delimita o campo seguinte com virgula.
  Serial.print(",");

  // Campo 5/8: aceleracao Z em g.
  Serial.print(a_z/2048);


  // Delimita o campo seguinte com virgula.
  Serial.print(",");

  // Campo 6/8: velocidade angular X em graus/s, usando a sensibilidade nominal de +/-2000 graus/s.
  Serial.print(Gyrx/16.4);
  // Delimita o campo seguinte com virgula.
  Serial.print(",");

  // Campo 7/8: velocidade angular Y em graus/s.
  Serial.print(Gyry/16.4);
  // Delimita o ultimo campo com virgula.
  Serial.print(",");

  // Campo 8/8: velocidade angular Z em graus/s e quebra de linha que fecha a amostra CSV.
  Serial.println(Gyrz/16.4);


}
