#include <iostream>
#include <string>
#include <chrono>
#include <thread>
#include <iomanip>
#include <fstream>
const bool DEBUG = false;
#ifdef _WIN32
#ifndef _WIN32_WINNT
#define _WIN32_WINNT 0x0600
#endif
#include <winsock2.h>
#include <ws2tcpip.h>
#include <windows.h>
#include <timeapi.h>
#pragma comment(lib, "winmm.lib")
#pragma comment(lib, "ws2_32.lib")
#include <cstdint>
#define close closesocket
#else
#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h>
#define SOCKET int
#define INVALID_SOCKET -1
#define closesocket close
#endif

#pragma pack(push, 1)
struct CovertPacket
{
    uint32_t sequence_number;
    uint8_t packet_type; // 0 = data, 1 = probe
};
#pragma pack(pop)

const auto MESSAGE_TIMEOUT = std::chrono::milliseconds(5000);

void precise_sleep_ms(double duration_ms)
{
#ifdef _WIN32
    Sleep((DWORD)duration_ms);
#else
    usleep((useconds_t)(duration_ms * 1000));
#endif
}

void run_probe_mode(const char *targetIp, int port, double probe_delay_ms, int packet_count)
{
    std::cout << "=== PROBE MODE ===" << std::endl;
    std::cout << "Target: " << targetIp << ":" << port << std::endl;
    std::cout << "Probe delay: " << probe_delay_ms << "ms" << std::endl;
    std::cout << "Packet count: " << packet_count << std::endl;
    std::cout << "==================" << std::endl;

#ifdef _WIN32
    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0)
    {
        std::cout << "WSAStartup failed" << std::endl;
        return;
    }
#endif

    SOCKET sendSocket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (sendSocket == INVALID_SOCKET)
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

    if (inet_pton(AF_INET, targetIp, &recvAddr.sin_addr) <= 0)
    {
        std::cout << "Invalid IP address: " << targetIp << std::endl;
        closesocket(sendSocket);
#ifdef _WIN32
        WSACleanup();
#endif
        return;
    }

    uint32_t seq_num = 0;
    int packets_sent = 0;

    std::cout << "Starting probe transmission..." << std::endl;

    auto test_start = std::chrono::high_resolution_clock::now();

    // Send initial packet immediately
    CovertPacket packet;
    packet.sequence_number = htonl(seq_num);
    packet.packet_type = 1; // Probe packet
    sendto(sendSocket, (const char *)&packet, sizeof(packet), 0, (sockaddr *)&recvAddr, sizeof(recvAddr));
    packets_sent++;
    seq_num++;

    auto last_send_time = std::chrono::high_resolution_clock::now();

    // Send remaining packets with precise timing
    while (packets_sent < packet_count)
    {
        precise_sleep_ms(probe_delay_ms);

        auto send_time = std::chrono::high_resolution_clock::now();
        packet.sequence_number = htonl(seq_num);
        packet.packet_type = 1;

        int bytesSent = sendto(sendSocket, (const char *)&packet, sizeof(packet), 0, (sockaddr *)&recvAddr, sizeof(recvAddr));

        if (bytesSent == -1)
        {
            std::cout << "Send failed for packet " << seq_num << std::endl;
        }
        else if (packets_sent % 500 == 0)
        {
            auto actual_interval = std::chrono::duration<double, std::milli>(send_time - last_send_time);
            std::cout << "Sent packet " << seq_num << " (Total: " << packets_sent
                      << ", Actual interval: " << std::fixed << std::setprecision(1)
                      << actual_interval.count() << "ms)" << std::endl;
        }

        last_send_time = send_time;
        packets_sent++;
        seq_num++;
    }

    auto test_end = std::chrono::high_resolution_clock::now();
    auto total_duration = std::chrono::duration<double>(test_end - test_start);

    std::cout << "\n=== PROBE COMPLETE ===" << std::endl;
    std::cout << "Total packets sent: " << packets_sent << std::endl;
    std::cout << "Total duration: " << std::fixed << std::setprecision(1) << total_duration.count() << " seconds" << std::endl;
    std::cout << "Average rate: " << (double)packets_sent / total_duration.count() << " packets/second" << std::endl;
    std::cout << "======================" << std::endl;

    closesocket(sendSocket);
#ifdef _WIN32
    WSACleanup();
#endif
}

int main(int argc, char *argv[])
{
#ifdef _WIN32
    timeBeginPeriod(1); // Set Windows timer resolution to 1ms
#endif
    // Check for probe mode
    if (argc >= 2 && std::string(argv[1]) == "-probe")
    {
        if (argc != 6)
        {
            std::cout << "Probe Mode Usage:" << std::endl;
            std::cout << "  " << argv[0] << " -probe <IP_ADDRESS> <PORT> <DELAY_MS> <PACKET_COUNT>" << std::endl;
            std::cout << "Example:" << std::endl;
            std::cout << "  " << argv[0] << " -probe 127.0.0.1 9090 20 5000" << std::endl;
            return 1;
        }

        const char *targetIp = argv[2];
        int port = atoi(argv[3]);
        double probe_delay_ms = atof(argv[4]);
        int packet_count = atoi(argv[5]);

        if (probe_delay_ms <= 0 || packet_count <= 0)
        {
            std::cout << "Error: Delay and packet count must be positive" << std::endl;
            return 1;
        }

        run_probe_mode(targetIp, port, probe_delay_ms, packet_count);
#ifdef _WIN32
        timeEndPeriod(1);
#endif
        return 0;
    }

    // Original covert channel mode
    if (argc != 4 && argc != 5 && argc != 6 && argc != 7)
    {
        std::cout << "Covert Channel Usage:" << std::endl;
        std::cout << "  " << argv[0] << " <IP_ADDRESS> <PORT> \"<MESSAGE>\" [ZERO_DELAY_MS] [ONE_DELAY_MS]" << std::endl;
        std::cout << "  " << argv[0] << " <IP_ADDRESS> <PORT> -f <FILENAME> [ZERO_DELAY_MS] [ONE_DELAY_MS]" << std::endl;
        std::cout << "Probe Mode Usage:" << std::endl;
        std::cout << "  " << argv[0] << " -probe <IP_ADDRESS> <PORT> <DELAY_MS> <PACKET_COUNT>" << std::endl;
        return 1;
    }

    const char *targetIp = argv[1];
    int port = atoi(argv[2]);
    std::string message;
    double zero_ms = 50.0; // Use double for milliseconds
    double one_ms = 150.0; // Use double for milliseconds

    if (std::string(argv[3]) == "-f")
    {
        if (argc < 5)
        {
            std::cout << "Error: Filename required after -f" << std::endl;
            return 1;
        }

        std::string filename = argv[4];
        std::ifstream file(filename);
        if (!file.is_open())
        {
            std::cout << "Error: Cannot open file " << filename << std::endl;
            return 1;
        }

        std::string line;
        while (std::getline(file, line))
        {
            message += line + "\n";
        }

        if (message.empty())
        {
            std::cout << "Error: File is empty" << std::endl;
            return 1;
        }

        if (!message.empty() && message.back() == '\n')
        {
            message.pop_back();
        }

        // Handle optional delay parameters for file mode
        if (argc >= 6)
            zero_ms = atof(argv[5]);
        if (argc >= 7)
            one_ms = atof(argv[6]);
    }
    else
    {
        // Regular message mode
        message = argv[3];
        if (argc >= 5)
            zero_ms = atof(argv[4]);
        if (argc >= 6)
            one_ms = atof(argv[5]);
    }

    if (zero_ms <= 0 || one_ms <= 0 || zero_ms >= one_ms)
    {
        std::cout << "Error: Invalid delays" << std::endl;
        return 1;
    }

    std::cout << "Using delays: " << zero_ms << "ms (0-bit), " << one_ms << "ms (1-bit)" << std::endl;

#ifdef _WIN32
    WSADATA wsaData;
    if (WSAStartup(MAKEWORD(2, 2), &wsaData) != 0)
    {
        std::cout << "WSAStartup failed" << std::endl;
        return 1;
    }
#endif

    SOCKET sendSocket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (sendSocket == INVALID_SOCKET)
    {
        std::cout << "Unable to create socket" << std::endl;
#ifdef _WIN32
        WSACleanup();
#endif
        return 1;
    }

    sockaddr_in recvAddr;
    recvAddr.sin_family = AF_INET;
    recvAddr.sin_port = htons(port);

    if (inet_pton(AF_INET, targetIp, &recvAddr.sin_addr) <= 0)
    {
        std::cout << "Invalid IP address: " << targetIp << std::endl;
        closesocket(sendSocket);
#ifdef _WIN32
        WSACleanup();
#endif
        return 1;
    }

    uint32_t seq_num = 0;
    int total_bits = message.length() * 8;

    std::cout << "=== TRANSMISSION ANALYSIS ===" << std::endl;
    std::cout << "Message: \"" << message << "\"" << std::endl;
    std::cout << "Message length: " << message.length() << " characters" << std::endl;
    std::cout << "Total bits to encode: " << total_bits << std::endl;

    auto transmission_start = std::chrono::high_resolution_clock::now();

    // Send first packet immediately
    CovertPacket packet;
    packet.sequence_number = htonl(seq_num);
    packet.packet_type = 0; // Data packet
    sendto(sendSocket, (const char *)&packet, sizeof(packet), 0, (sockaddr *)&recvAddr, sizeof(recvAddr));
    std::cout << "Sent initial packet, Seq Num: " << seq_num << std::endl;
    seq_num++;

    // Encode message - ALL IN MILLISECONDS
    for (char c : message)
    {
        std::cout << "Encoding character: '" << c << "' (ASCII " << (int)c << ")" << std::endl;
        for (int i = 7; i >= 0; --i)
        {
            int bit = (c >> i) & 1;
            double target_delay_ms = (bit == 0) ? zero_ms : one_ms;

            auto sleep_start = std::chrono::high_resolution_clock::now();
            precise_sleep_ms(target_delay_ms);
            auto sleep_end = std::chrono::high_resolution_clock::now();

            auto actual_delay = std::chrono::duration<double, std::milli>(sleep_end - sleep_start);
            double actual_delay_ms = actual_delay.count();

            packet.sequence_number = htonl(seq_num);
            packet.packet_type = 0;

            int bytesSent = sendto(sendSocket, (const char *)&packet, sizeof(packet), 0, (sockaddr *)&recvAddr, sizeof(recvAddr));
            if (bytesSent == -1)
            {
                std::cout << "Send failed for packet " << seq_num << std::endl;
            }
            else
            {
                std::cout << "Sent Seq Num: " << seq_num << ", Bit: " << bit
                          << " (Target: " << std::fixed << std::setprecision(1) << target_delay_ms
                          << "ms, Actual: " << actual_delay_ms << "ms)" << std::endl;
            }
            seq_num++;
        }
    }

    auto transmission_end = std::chrono::high_resolution_clock::now();
    auto total_time = std::chrono::duration<double, std::milli>(transmission_end - transmission_start);

    std::cout << "\n=== TRANSMISSION COMPLETE ===" << std::endl;
    std::cout << "Total time: " << std::fixed << std::setprecision(1) << total_time.count() << "ms" << std::endl;

    closesocket(sendSocket);
#ifdef _WIN32
    WSACleanup();
    timeEndPeriod(1);
#endif

    return 0;
}