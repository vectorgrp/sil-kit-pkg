/*
*
* SPDX-FileCopyrightText: 2024 Vector Informatik GmbH
*
* SPDX-License-Identifier: MIT
*/
#include <iostream>

#include "silkit/SilKit.hpp"


int main(void) {

    try
    {
        auto participantConfig = SilKit::Config::ParticipantConfigurationFromString("{}");
        auto participant = SilKit::CreateParticipant(participantConfig, "TestClient","silkit://localhost:8500");
        return 0;
    }
    catch (const std::exception& error)
    {
        std::cerr << "Something went wrong: " << error.what() << std::endl;
        std::cerr << "Exiting!" << std::endl;
        return 1;
    }
}
