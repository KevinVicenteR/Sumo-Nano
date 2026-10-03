#ifndef ISENSOR_H
#define ISENSOR_H

class ISensor {
public:
    virtual ~ISensor() {}
    virtual bool detectar() = 0;
};

#endif // ISENSOR_H
