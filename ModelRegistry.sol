// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/// @title ModelRegistry — ChainML
/// @notice Stores SHA-256 hashes of ML model submissions permanently on-chain.
/// Deploy once on Ethereum Sepolia testnet via Remix IDE.
contract ModelRegistry {
    struct Submission {
        bytes32 dataHash;
        address submitter;
        uint256 timestamp;
        string  projectId;
    }
    Submission[] public submissions;
    event ModelSubmitted(bytes32 indexed dataHash, address indexed submitter, string projectId, uint256 timestamp);

    function submitModel(bytes32 dataHash, string calldata projectId) external {
        submissions.push(Submission(dataHash, msg.sender, block.timestamp, projectId));
        emit ModelSubmitted(dataHash, msg.sender, projectId, block.timestamp);
    }
    function getSubmission(uint256 index) external view returns (Submission memory) {
        require(index < submissions.length, "Out of bounds");
        return submissions[index];
    }
    function totalSubmissions() external view returns (uint256) {
        return submissions.length;
    }
}
