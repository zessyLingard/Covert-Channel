#include <iostream>
#include <chrono>
#include <string>
#include <iomanip>
#include <fstream>

#ifdef _WIN32
    #ifndef _WIN32_WINNT
        #define _WIN32_WINNT 0x0600
    #endif
    #define WIN32_LEAN_AND_MEAN
    #include <winsock2.h>
    #include <ws2tcpip.h>
    #include <cstdint> 
    #define close closesocket
    typedef int socklen_t;
#else
    #include <sys/socket.h>
    #include <arpa/inet.h>
    #include <unistd.h>
    #define SOCKET int
    #define INVALID_SOCKET -1
    #define closesocket close
#endif

#pragma pack(push, 1)
struct CovertPacket {
    uint32_t sequence_number;
    uint8_t packet_type; // 0 = data, 1 = probe
};
#pragma pack(pop)

const auto MESSAGE_TIMEOUT = std::chrono::milliseconds(5000);

void run_logging_mode(int port, const std::string& logfile)
{
    std::cout << "=== LOGGING MODE ===" << std::endl;
    std::cout << "Port: " << port << std::endl;
    std::cout << "Log file: " << logfile << std::endl;
    std::cout << "====================" << std::endl;

    std::ofstream log(logfile);
    if (!log.is_open())
    {
        std::cout << "Error: Cannot open log file " << logfile << std::endl;
        return;
    }

    log << "Time" << std::endl;

#ifdef _WIN32
    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0)
    {
        std::cout << "WSAStartup failed" << std::endl;
        return;
    }
#endif

    SOCKET recvSocket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (recvSocket == INVALID_SOCKET)
    {
        std::cout << "Unable to create socket" << std::endl;
#ifdef _WIN32
        WSACleanup();
#endif
        return;
    }

    sockaddr_in recvAddr;
    recvAddr.sin_family = AF_INET;
    recvAddr.sin_port = htons(port);
    recvAddr.sin_addr.s_addr = INADDR_ANY;

    if (bind(recvSocket, (sockaddr*)&recvAddr, sizeof(recvAddr)) == -1)
    {
        std::cout << "Bind failed." << std::endl;
        closesocket(recvSocket);
#ifdef _WIN32
        WSACleanup();
#endif
        return;
    }

    std::cout << "Logging receiver waiting for packets..." << std::endl;
    std::cout << "Press Ctrl+C to stop logging." << std::endl;

    CovertPacket packet;
    sockaddr_in senderAddr;
    socklen_t senderAddrSize = sizeof(senderAddr);

    auto last_arrival_time = std::chrono::high_resolution_clock::now();
    bool first_packet = true;
    int packets_logged = 0;

    while (true)
    {
        int bytesReceived = recvfrom(recvSocket, (char*)&packet, sizeof(packet), 0, (sockaddr*)&senderAddr, &senderAddrSize);
        if (bytesReceived > 0)
        {
            auto arrival_time = std::chrono::high_resolution_clock::now();
            uint32_t seq_num = ntohl(packet.sequence_number);
            uint8_t pkt_type = packet.packet_type;

            if (first_packet)
            {
                std::cout << "First packet received (Seq: " << seq_num << ", Type: " << (int)pkt_type << ")" << std::endl;
                log << "0.0" << std::endl;
                first_packet = false;
            }
            else
            {
                auto inter_arrival_time = std::chrono::duration<double, std::milli>(arrival_time - last_arrival_time);
                double iat_ms = inter_arrival_time.count();

                log << std::fixed << std::setprecision(3) << iat_ms << std::endl;


                if (packets_logged % 1000 == 0)
                {
                    std::cout << "Logged packet " << seq_num << " (Total: " << packets_logged + 1 
                             << ", IAT: " << std::fixed << std::setprecision(1) << iat_ms << "ms)" << std::endl;
                }
            }

            last_arrival_time = arrival_time;
            packets_logged++;

            if (packets_logged % 100 == 0)
            {
                log.flush();
            }
        }
    }

    // Clean up
    closesocket(recvSocket);
#ifdef _WIN32
    WSACleanup();
#endif
    
    // Temporarily undefine the macro to allow log.close()
#ifdef _WIN32
    #undef close
#endif
    log.close();
#ifdef _WIN32
    #define close closesocket  // Restore the macro
#endif
}

void run_decode_mode(int port, double threshold_ms)
{
    std::cout << "=== DECODE MODE ===" << std::endl;
    std::cout << "Port: " << port << std::endl;
    std::cout << "Threshold: " << threshold_ms << "ms" << std::endl;
    std::cout << "==================" << std::endl;

#ifdef _WIN32
    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0) {
        std::cout << "WSAStartup failed" << std::endl;
        return;
    }
#endif

    SOCKET recvSocket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (recvSocket == INVALID_SOCKET) {
        std::cout << "Unable to create socket" << std::endl;
#ifdef _WIN32
        WSACleanup();
#endif
        return;
    }

    sockaddr_in recvAddr;
    recvAddr.sin_family = AF_INET;
    recvAddr.sin_port = htons(port);
    recvAddr.sin_addr.s_addr = INADDR_ANY; 

    if (bind(recvSocket, (sockaddr*)&recvAddr, sizeof(recvAddr)) == -1) {
        std::cout << "Bind failed." << std::endl;
        closesocket(recvSocket);
#ifdef _WIN32
        WSACleanup();
#endif
        return;
    }
    
    std::cout << "Receiver waiting for packets..." << std::endl;
    
    CovertPacket packet;
    sockaddr_in senderAddr;
    socklen_t senderAddrSize = sizeof(senderAddr);

    auto last_arrival_time = std::chrono::high_resolution_clock::now();
    bool first_packet = true;
    
    std::string decoded_message = "";
    uint8_t current_byte = 0;
    int bit_count = 0;
    uint32_t last_seq_num = 0;
    
    auto message_start_time = std::chrono::high_resolution_clock::now();
    int total_packets_received = 0;

    while (true) {
        int bytesReceived = recvfrom(recvSocket, (char*)&packet, sizeof(packet), 0, (sockaddr*)&senderAddr, &senderAddrSize);
        if (bytesReceived > 0) {
            auto arrival_time = std::chrono::high_resolution_clock::now();
            uint32_t seq_num = ntohl(packet.sequence_number);

            bool is_new_message = false;
            
            if (!first_packet) {
                auto time_since_last = std::chrono::duration<double, std::milli>(arrival_time - last_arrival_time);
                
                if (time_since_last.count() > 5000.0 || seq_num <= last_seq_num) {
                    is_new_message = true;
                }
            }
            
            if (first_packet || is_new_message) {
                if (is_new_message && !decoded_message.empty()) {
                    auto message_end_time = std::chrono::high_resolution_clock::now();
                    auto total_time = std::chrono::duration<double, std::milli>(message_end_time - message_start_time);
                    
                    std::cout << "\n=== MESSAGE COMPLETE ===" << std::endl;
                    std::cout << "Final message: \"" << decoded_message << "\"" << std::endl;
                    std::cout << "Message length: " << decoded_message.length() << " characters" << std::endl;
                    std::cout << "Total time: " << std::fixed << std::setprecision(1) << total_time.count() << "ms" << std::endl;
                    std::cout << "=======================" << std::endl;
                }
                
                decoded_message = "";
                current_byte = 0;
                bit_count = 0;
                first_packet = false;
                total_packets_received = 0;
                message_start_time = arrival_time;
                
                std::cout << "Received initial packet with Seq Num: " << seq_num << std::endl;
            } else {
                if (packet.packet_type == 0) { // Only decode data packets
                    auto inter_arrival_time = std::chrono::duration<double, std::milli>(arrival_time - last_arrival_time);
                    double time_diff_ms = inter_arrival_time.count();
                    
                    int decoded_bit = (time_diff_ms < threshold_ms) ? 0 : 1;
                    
                    current_byte = (current_byte << 1) | decoded_bit;
                    bit_count++;
                    
                    std::cout << "Seq: " << seq_num << ", Time: " << std::fixed << std::setprecision(1) 
                             << time_diff_ms << "ms, Bit: " << decoded_bit << std::endl;

                    if (bit_count == 8) {
                        if (current_byte != 0) {  
                            decoded_message += (char)current_byte;
                            std::cout << "Decoded character: '" << (char)current_byte 
                                     << "' - Message so far: \"" << decoded_message << "\"" << std::endl;
                        }
                        current_byte = 0;
                        bit_count = 0;
                    }
                }
            }
            
            last_arrival_time = arrival_time;
            last_seq_num = seq_num;
            total_packets_received++;
        }
    }

    closesocket(recvSocket);
#ifdef _WIN32
    WSACleanup();
#endif
}

int main(int argc, char *argv[]) {
    // Check for logging mode flag
    if (argc >= 2 && std::string(argv[1]) == "-log")
    {
        if (argc != 4)
        {
            std::cout << "Logging Mode Usage:" << std::endl;
            std::cout << "  " << argv[0] << " -log <PORT> <LOGFILE>" << std::endl;
            std::cout << "Example:" << std::endl;
            std::cout << "  " << argv[0] << " -log 9090 jitter_log.csv" << std::endl;
            return 1;
        }
        
        int port = atoi(argv[2]);
        std::string logfile = argv[3];
        
        run_logging_mode(port, logfile);
        return 0;
    }

    // Default decode mode
    if (argc != 2 && argc != 3) { 
        std::cout << "Decode Mode Usage:" << std::endl;
        std::cout << "  " << argv[0] << " <PORT> [THRESHOLD_MS]" << std::endl;
    }
    
    int port = atoi(argv[1]);
    double threshold_ms = 125.0;
    if (argc == 3) {
        threshold_ms = atof(argv[2]);
    }
    
    run_decode_mode(port, threshold_ms);
    return 0;
}