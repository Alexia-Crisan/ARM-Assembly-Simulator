; Test program for stack operations (PSH / POP)
        ; Tests single and multiple register forms
        ; Uses R0–R10, ends with HLT

        ; ---------- Initialize ----------
        MOV     R0, #0x11        ; R0 = 0x11
        MOV     R1, #0x22        ; R1 = 0x22
        MOV     R2, #0x33        ; R2 = 0x33
        MOV     R3, #0x44        ; R3 = 0x44
        MOV     R4, #0x55        ; R4 = 0x55
        MOV     R5, #0x66        ; R5 = 0x66
        MOV     R6, #0x77        ; R6 = 0x77

        ; ---------- Single register PSH / POP ----------
        PSH     {R0}             ; push R0
        PSH     {R1}             ; push R1
        PSH     {R2}             ; push R2

        ; POP them back in reverse order
        POP     {R10}            ; should get 0x33 (R2)
        POP     {R9}             ; should get 0x22 (R1)
        POP     {R8}             ; should get 0x11 (R0)

        ; ---------- Multi-register PSH / POP ----------
        PSH     {R3, R4, R5, R6} 
        POP     {R0, R1, R2, R3} 

        ; ---------- End of test ----------
        HLT                    