        MOV R0, #1
        MOV R1, #2
        JMS subroutine
        ADD R2, R0, R1
        HLT

subroutine:
        ADD R0, #5
        RET
