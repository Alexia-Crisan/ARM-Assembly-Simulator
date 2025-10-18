; Input: N in R0
; Output: sum in R1

MOV R0, #6
MOV R1, #0      ; sum = 0
MOV R2, #1      ; counter = 1

sum_loop:
CMP R2, R0      ; compare counter with N
BGT end_sum     ; if counter > N, exit loop

ADD R1, R1, R2  ; sum += counter
ADD R2, R2, #1  ; counter++

B sum_loop      ; repeat loop

end_sum:
; result in R1
